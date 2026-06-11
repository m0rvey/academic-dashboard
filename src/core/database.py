import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.core.config import MAX_BACKUPS
from src.core.interfaces import IDatabaseManager
from src.core.logger import setup_logger
from src.core.models import Task, TaskStatus

logger = setup_logger("database")


def get_period_dates(period: str) -> tuple:
    from datetime import date, timedelta

    today = date.today()
    if period == "today":
        return today.isoformat(), today.isoformat()
    elif period == "week":
        return (today - timedelta(days=6)).isoformat(), today.isoformat()
    elif period == "month":
        return (today - timedelta(days=29)).isoformat(), today.isoformat()
    return None, None


class DatabaseManager(IDatabaseManager):
    """Управление базой данных SQLite3 для учебных задач."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn = None
        self._lock = threading.Lock()

    def _notify_change(self) -> None:
        """Обновляет время изменения базы данных с помощью файла-триггера."""
        try:
            trigger_path = self.db_path.parent / ".db_change"
            trigger_path.parent.mkdir(parents=True, exist_ok=True)
            trigger_path.touch(exist_ok=True)
        except OSError as e:
            logger.warning(f"Error in _notify_change: {e}")

    @contextmanager
    def _connection(self):
        """Возвращает существующее соединение с БД под блокировкой."""
        # Автоматически создаем директорию для базы данных, если она отсутствует
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            if self._conn is None:
                self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
                self._conn.row_factory = sqlite3.Row
                # Включение режима WAL для повышения производительности и безопасности при конкурентном доступе
                self._conn.execute("PRAGMA journal_mode = WAL;")
                # Включение внешних ключей для поддержки каскадного удаления
                self._conn.execute("PRAGMA foreign_keys = ON;")
            yield self._conn

    def close(self) -> None:
        """Закрывает соединение с базой данных."""
        if hasattr(self, "_lock"):
            with self._lock:
                conn = self._conn
                self._conn = None
                if conn is not None:
                    conn.close()

    def init_db(self) -> None:
        """Инициализирует структуру базы данных и выполняет миграцию при необходимости."""
        from src.core.migrations import run_migrations

        with self._connection() as conn:
            try:
                run_migrations(conn)
                conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
                raise e

    def _get_tags_for_tasks(self, conn, task_ids: List[int]) -> dict:
        """Получает теги для списка ID задач за один запрос (предотвращает N+1)."""
        if not task_ids:
            return {}
        placeholders = ",".join("?" for _ in task_ids)
        query = f"""
            SELECT tt.task_id, t.name
            FROM task_tags tt
            JOIN tags t ON tt.tag_id = t.id
            WHERE tt.task_id IN ({placeholders})
        """
        cursor = conn.execute(query, task_ids)
        result = {}
        for row in cursor.fetchall():
            result.setdefault(row["task_id"], []).append(row["name"])
        return result

    def _row_to_task(self, row: sqlite3.Row, tags: Optional[List[str]] = None) -> Task:
        """Преобразует строку БД в объект Task."""
        if tags is None:
            tags = []
        try:
            grade = row["grade"]
        except (IndexError, KeyError):
            grade = None
        return Task(
            id=row["id"],
            subject=row["subject"],
            description=row["description"],
            deadline=row["deadline"],
            effort_score=row["effort_score"],
            tags=tags,
            status=TaskStatus(row["status"]),
            grade=grade,
        )

    def add_task(self, task: Task, notify: bool = True) -> int:
        """Добавляет задачу в базу данных и возвращает её ID."""
        with self._connection() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO tasks (subject, description, deadline, effort_score, status, grade)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task.subject,
                        task.description,
                        task.deadline,
                        task.effort_score,
                        task.status.value,
                        task.grade,
                    ),
                )
                task_id = cursor.lastrowid

                # Вставляем теги Many-to-Many
                for tag_name in task.tags:
                    conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
                    tag_cursor = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
                    tag_row = tag_cursor.fetchone()
                    if tag_row:
                        tag_id = tag_row["id"]
                        conn.execute(
                            "INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)",
                            (task_id, tag_id),
                        )

                conn.commit()
                if notify:
                    self._notify_change()
                return task_id
            except sqlite3.Error as e:
                conn.rollback()
                raise e

    def get_all_tasks(self) -> List[Task]:
        """Получает все задачи из базы данных."""
        with self._connection() as conn:
            cursor = conn.execute("SELECT id, subject, description, deadline, effort_score, status, grade FROM tasks")
            rows = cursor.fetchall()
            if not rows:
                return []
            task_ids = [row["id"] for row in rows]
            tags_map = self._get_tags_for_tasks(conn, task_ids)
            return [self._row_to_task(row, tags_map.get(row["id"], [])) for row in rows]

    def get_active_tasks(self) -> List[Task]:
        """Получает только невыполненные задачи из базы данных."""
        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT id, subject, description, deadline, effort_score, status, grade FROM tasks WHERE status != 2"
            )
            rows = cursor.fetchall()
            if not rows:
                return []
            task_ids = [row["id"] for row in rows]
            tags_map = self._get_tags_for_tasks(conn, task_ids)
            return [self._row_to_task(row, tags_map.get(row["id"], [])) for row in rows]

    def get_tasks_with_grades(self) -> List[Task]:
        """Получает только выполненные задачи, у которых выставлена оценка."""
        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT id, subject, description, deadline, effort_score, status, grade FROM tasks WHERE status = 2 AND grade IS NOT NULL"
            )
            rows = cursor.fetchall()
            if not rows:
                return []
            task_ids = [row["id"] for row in rows]
            tags_map = self._get_tags_for_tasks(conn, task_ids)
            return [self._row_to_task(row, tags_map.get(row["id"], [])) for row in rows]

    def update_task_status(self, task_id: int, status: TaskStatus) -> bool:
        """Обновляет статус задачи по её ID. Возвращает True в случае успеха."""
        with self._connection() as conn:
            try:
                cursor = conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status.value, task_id))
                updated = cursor.rowcount > 0
                conn.commit()
                if updated:
                    self._notify_change()
                return updated
            except sqlite3.Error as e:
                conn.rollback()
                raise e

    def update_task_grade(self, task_id: int, grade: Optional[int]) -> bool:
        """Обновляет оценку задачи по её ID. Возвращает True в случае успеха."""
        with self._connection() as conn:
            try:
                cursor = conn.execute("UPDATE tasks SET grade = ? WHERE id = ?", (grade, task_id))
                updated = cursor.rowcount > 0
                conn.commit()
                if updated:
                    self._notify_change()
                return updated
            except sqlite3.Error as e:
                conn.rollback()
                raise e

    def update_task(self, task: Task) -> bool:
        """Обновляет всю информацию о задаче."""
        with self._connection() as conn:
            try:
                cursor = conn.execute(
                    """
                    UPDATE tasks
                    SET subject = ?, description = ?, deadline = ?, effort_score = ?, status = ?, grade = ?
                    WHERE id = ?
                    """,
                    (
                        task.subject,
                        task.description,
                        task.deadline,
                        task.effort_score,
                        task.status.value,
                        task.grade,
                        task.id,
                    ),
                )
                updated = cursor.rowcount > 0

                # Обновляем теги: удаляем старые связи, вставляем новые
                conn.execute("DELETE FROM task_tags WHERE task_id = ?", (task.id,))
                for tag_name in task.tags:
                    conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
                    tag_cursor = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
                    tag_row = tag_cursor.fetchone()
                    if tag_row:
                        tag_id = tag_row["id"]
                        conn.execute(
                            "INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)",
                            (task.id, tag_id),
                        )

                # Удаляем теги-сироты
                conn.execute("DELETE FROM tags WHERE id NOT IN (SELECT DISTINCT tag_id FROM task_tags)")

                conn.commit()
                if updated:
                    self._notify_change()
                return updated
            except sqlite3.Error as e:
                conn.rollback()
                raise e

    def delete_task(self, task_id: int) -> bool:
        """Удаляет задачу по ID."""
        with self._connection() as conn:
            try:
                cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                deleted = cursor.rowcount > 0
                if deleted:
                    # Удаляем теги-сироты
                    conn.execute("DELETE FROM tags WHERE id NOT IN (SELECT DISTINCT tag_id FROM task_tags)")
                conn.commit()
                if deleted:
                    self._notify_change()
                return deleted
            except sqlite3.Error as e:
                conn.rollback()
                raise e

    def export_to_json(self, filepath: str) -> None:
        """Экспортирует все задачи в JSON файл."""
        path = Path(filepath)
        # Создаем родительскую директорию, если она отсутствует
        path.parent.mkdir(parents=True, exist_ok=True)

        tasks = self.get_all_tasks()
        data = []
        for task in tasks:
            data.append(
                {
                    "id": task.id,
                    "subject": task.subject,
                    "description": task.description,
                    "deadline": task.deadline,
                    "effort_score": task.effort_score,
                    "tags": task.tags,
                    "status": task.status.value,
                    "grade": task.grade,
                }
            )
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def import_from_json(self, filepath: str) -> None:
        """Импортирует задачи из JSON файла (добавляет к существующим)."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Файл бэкапа не найден по пути: {filepath}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("Неверный формат данных JSON: ожидается список задач.")

        imported_any = False
        for item in data:
            # Валидация структуры
            if not all(
                k in item
                for k in (
                    "subject",
                    "description",
                    "deadline",
                    "effort_score",
                    "status",
                )
            ):
                continue

            try:
                status_val = int(item["status"])
                if status_val not in (0, 1, 2):
                    status_val = 0
                status = TaskStatus(status_val)
            except (ValueError, KeyError, TypeError):
                status = TaskStatus.TODO

            grade_val = item.get("grade", None)
            if grade_val is not None:
                try:
                    grade_val = int(grade_val)
                    if grade_val not in (2, 3, 4, 5):
                        grade_val = None
                except (ValueError, TypeError):
                    grade_val = None

            task = Task(
                subject=str(item["subject"]),
                description=str(item["description"]),
                deadline=str(item["deadline"]),
                effort_score=max(1, int(item["effort_score"])),
                tags=[str(t).strip() for t in item.get("tags", []) if str(t).strip()],
                status=status,
                grade=grade_val,
            )
            self.add_task(task, notify=False)
            imported_any = True

        if imported_any:
            self._notify_change()

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Получает задачу по её ID. Возвращает None, если задача не найдена."""
        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT id, subject, description, deadline, effort_score, status, grade FROM tasks WHERE id = ?",
                (task_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            tags_cursor = conn.execute(
                """
                SELECT t.name FROM tags t
                JOIN task_tags tt ON t.id = tt.tag_id
                WHERE tt.task_id = ?
                """,
                (task_id,),
            )
            tags = [r["name"] for r in tags_cursor.fetchall()]
            return self._row_to_task(row, tags)

    def register_user(self, chat_id: int) -> None:
        """Регистрирует chat_id пользователя Telegram в базе данных."""
        with self._connection() as conn:
            try:
                conn.execute("INSERT OR IGNORE INTO bot_users (chat_id) VALUES (?)", (chat_id,))
                conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
                raise e

    def get_all_tags(self) -> List[str]:
        """Получает список всех уникальных тегов из базы данных."""
        with self._connection() as conn:
            cursor = conn.execute("SELECT name FROM tags ORDER BY name ASC")
            return [row["name"] for row in cursor.fetchall()]

    def get_all_users(self) -> List[int]:
        """Получает список всех зарегистрированных chat_id пользователей."""
        with self._connection() as conn:
            cursor = conn.execute("SELECT chat_id FROM bot_users")
            return [row["chat_id"] for row in cursor.fetchall()]

    def unregister_user(self, chat_id: int) -> bool:
        """Удаляет chat_id пользователя из базы данных."""
        with self._connection() as conn:
            try:
                cursor = conn.execute("DELETE FROM bot_users WHERE chat_id = ?", (chat_id,))
                updated = cursor.rowcount > 0
                conn.commit()
                return updated
            except sqlite3.Error as e:
                conn.rollback()
                raise e

    def get_filtered_tasks(
        self,
        search_query: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        tag: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> List[Task]:
        """Получает отфильтрованные и отсортированные задачи непосредственно из БД."""
        query = (
            "SELECT DISTINCT t.id, t.subject, t.description, t.deadline, t.effort_score, t.status, t.grade FROM tasks t"
        )
        params = []
        where_clauses = []

        if tag:
            query += " JOIN task_tags tt ON t.id = tt.task_id JOIN tags tg ON tt.tag_id = tg.id"
            where_clauses.append("tg.name = ?")
            params.append(tag)

        if status is not None:
            where_clauses.append("t.status = ?")
            params.append(status.value)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        from src.core.config import EXAM_PRIORITY_MULTIPLIER, EXAM_TAGS

        if sort_by == "deadline":
            query += " ORDER BY t.deadline ASC"
        elif sort_by == "effort":
            query += " ORDER BY t.effort_score DESC"
        elif sort_by == "priority" or not sort_by:
            exam_placeholders = ", ".join("?" for _ in EXAM_TAGS)
            query += f""" ORDER BY (
                CAST(t.effort_score AS REAL) / (
                    (CASE
                        WHEN (julianday(t.deadline) - julianday(date('now', 'localtime'))) < 0 THEN 0
                        ELSE CAST(julianday(t.deadline) - julianday(date('now', 'localtime')) AS INTEGER)
                    END) + 1
                ) * CASE
                    WHEN EXISTS (
                        SELECT 1 FROM task_tags tt2
                        JOIN tags tg2 ON tt2.tag_id = tg2.id
                        WHERE tt2.task_id = t.id AND tg2.name IN ({exam_placeholders})
                    ) THEN {EXAM_PRIORITY_MULTIPLIER}
                    ELSE 1.0
                END
            ) DESC"""
            params.extend(EXAM_TAGS)

        with self._connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            if not rows:
                return []
            task_ids = [row["id"] for row in rows]
            tags_map = self._get_tags_for_tasks(conn, task_ids)
            tasks = [self._row_to_task(row, tags_map.get(row["id"], [])) for row in rows]

            # Фильтрация по поисковому запросу в Python для поддержки кириллицы
            if search_query:
                q = search_query.lower()
                tasks = [t for t in tasks if q in t.subject.lower() or q in t.description.lower()]

            # Сортировка по названию (с поддержкой кириллицы) в Python
            if sort_by == "subject":
                tasks.sort(key=lambda t: t.subject.lower())

            return tasks

    def get_daily_load_for_date(self, target_date: str) -> tuple:
        """Вычисляет суммарную нагрузку на указанную дату на уровне БД.
        Возвращает кортеж (total_load, is_overloaded).
        """
        from datetime import date

        from src.core.config import DAILY_LOAD_LIMIT
        from src.core.models import get_clean_date

        try:
            target_date_obj = date.fromisoformat(get_clean_date(target_date))
        except ValueError:
            target_date_obj = date.today()

        target_date_str = target_date_obj.isoformat()

        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT SUM(effort_score) as total FROM tasks WHERE deadline = ? AND status != 2",
                (target_date_str,),
            )
            row = cursor.fetchone()
            total_load = row["total"] if row["total"] is not None else 0
            return total_load, total_load > DAILY_LOAD_LIMIT

    def get_kpi_stats(self, period: str = "all") -> dict:
        """Получает агрегированную KPI-статистику по задачам."""
        from datetime import date

        from src.core.config import EXAM_PRIORITY_MULTIPLIER, EXAM_TAGS

        today_str = date.today().isoformat()
        start_date, end_date = get_period_dates(period)

        where_clause = ""
        params = []
        if start_date and end_date:
            where_clause = " WHERE deadline BETWEEN ? AND ?"
            params = [start_date, end_date]

        exam_placeholders = ", ".join("?" for _ in EXAM_TAGS)
        priority_expr = f"""(
            CAST(effort_score AS REAL) / (
                (CASE
                    WHEN (julianday(deadline) - julianday(date('now', 'localtime'))) < 0 THEN 0
                    ELSE CAST(julianday(deadline) - julianday(date('now', 'localtime')) AS INTEGER)
                END) + 1
            ) * CASE
                WHEN EXISTS (
                    SELECT 1 FROM task_tags tt2
                    JOIN tags tg2 ON tt2.tag_id = tg2.id
                    WHERE tt2.task_id = tasks.id AND tg2.name IN ({exam_placeholders})
                ) THEN {EXAM_PRIORITY_MULTIPLIER}
                ELSE 1.0
            END
        )"""

        # Объединяем count-запросы в один
        query = f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status != 2 AND deadline < ? THEN 1 ELSE 0 END) as overdue,
                SUM(CASE WHEN status != 2 AND {priority_expr} >= 2.5 THEN 1 ELSE 0 END) as high_priority
            FROM tasks
            {where_clause}
        """
        query_params = [today_str] + list(EXAM_TAGS) + params

        with self._connection() as conn:
            row = conn.execute(query, query_params).fetchone()
            total = row["total"] if row["total"] is not None else 0
            completed = row["completed"] if row["completed"] is not None else 0
            overdue = row["overdue"] if row["overdue"] is not None else 0
            high_priority_count = row["high_priority"] if row["high_priority"] is not None else 0

            return {
                "total": total,
                "completed": completed,
                "overdue": overdue,
                "high_priority": high_priority_count,
            }

    def get_subject_load(self, period: str = "all") -> dict:
        """Получает распределение нагрузки по предметам."""
        start_date, end_date = get_period_dates(period)
        query = "SELECT subject, SUM(effort_score) as load FROM tasks WHERE status != 2"
        params = []
        if start_date and end_date:
            query += " AND deadline BETWEEN ? AND ?"
            params = [start_date, end_date]
        query += " GROUP BY subject"

        with self._connection() as conn:
            cursor = conn.execute(query, params)
            return {row["subject"]: row["load"] for row in cursor.fetchall()}

    def get_tag_load(self, period: str = "all") -> dict:
        """Получает распределение нагрузки по тегам."""
        start_date, end_date = get_period_dates(period)
        query = """
            SELECT tg.name, SUM(t.effort_score) as load
            FROM tasks t
            JOIN task_tags tt ON t.id = tt.task_id
            JOIN tags tg ON tt.tag_id = tg.id
            WHERE t.status != 2
        """
        params = []
        if start_date and end_date:
            query += " AND t.deadline BETWEEN ? AND ?"
            params = [start_date, end_date]
        query += " GROUP BY tg.name"

        with self._connection() as conn:
            cursor = conn.execute(query, params)
            return {row["name"]: row["load"] for row in cursor.fetchall()}

    def get_completed_tasks_by_day_last_7_days(self) -> dict:
        """Получает количество выполненных задач по дням за последние 7 дней (от date('now', '-6 days') до date('now'))."""
        from datetime import date, timedelta

        today = date.today()
        result = {}
        # Инициализируем последние 7 дней нулями
        for i in range(7):
            d = today - timedelta(days=6 - i)
            result[d.isoformat()] = 0

        with self._connection() as conn:
            cursor = conn.execute(
                """
                SELECT deadline, COUNT(*) as count
                FROM tasks
                WHERE status = 2 AND deadline BETWEEN ? AND ?
                GROUP BY deadline
                """,
                ((today - timedelta(days=6)).isoformat(), today.isoformat()),
            )
            for row in cursor.fetchall():
                d_str = row["deadline"]
                if d_str in result:
                    result[d_str] = row["count"]
        return result

    def get_grades_stats(self) -> dict:
        """Получает общую успеваемость."""
        with self._connection() as conn:
            cursor = conn.execute("""
                SELECT
                    COUNT(grade) as total_count,
                    AVG(grade) as gpa,
                    SUM(CASE WHEN grade = 5 THEN 1 ELSE 0 END) as count_5,
                    SUM(CASE WHEN grade = 4 THEN 1 ELSE 0 END) as count_4,
                    SUM(CASE WHEN grade = 3 THEN 1 ELSE 0 END) as count_3,
                    SUM(CASE WHEN grade = 2 THEN 1 ELSE 0 END) as count_2
                FROM tasks
                WHERE status = 2 AND grade IS NOT NULL
                """)
            row = cursor.fetchone()
            if not row or row["total_count"] == 0:
                return {}
            return {
                "total_count": row["total_count"],
                "gpa": row["gpa"],
                "count_5": row["count_5"],
                "count_4": row["count_4"],
                "count_3": row["count_3"],
                "count_2": row["count_2"],
            }

    def get_subject_grades_gpa(self) -> dict:
        """Получает средний балл по каждому предмету."""
        with self._connection() as conn:
            cursor = conn.execute("""
                SELECT subject, AVG(grade) as gpa, COUNT(grade) as count
                FROM tasks
                WHERE status = 2 AND grade IS NOT NULL
                GROUP BY subject
                """)
            return {row["subject"]: {"gpa": row["gpa"], "count": row["count"]} for row in cursor.fetchall()}

    def get_overdue_tasks(self, today_date_str: str) -> List[Task]:
        """Получает все просроченные невыполненные задачи на указанную дату."""
        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT id, subject, description, deadline, effort_score, status, grade FROM tasks WHERE status != 2 AND deadline < ?",
                (today_date_str,),
            )
            rows = cursor.fetchall()
            if not rows:
                return []
            task_ids = [row["id"] for row in rows]
            tags_map = self._get_tags_for_tasks(conn, task_ids)
            return [self._row_to_task(row, tags_map.get(row["id"], [])) for row in rows]

    def get_tasks_by_date(self, target_date_str: str) -> List[Task]:
        """Получает все невыполненные задачи на указанную дату."""
        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT id, subject, description, deadline, effort_score, status, grade FROM tasks WHERE status != 2 AND deadline = ?",
                (target_date_str,),
            )
            rows = cursor.fetchall()
            if not rows:
                return []
            task_ids = [row["id"] for row in rows]
            tags_map = self._get_tags_for_tasks(conn, task_ids)
            return [self._row_to_task(row, tags_map.get(row["id"], [])) for row in rows]

    def get_all_tasks_by_date(self, target_date_str: str) -> List[Task]:
        """Получает абсолютно все задачи (включая выполненные) на указанную дату дедлайна."""
        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT id, subject, description, deadline, effort_score, status, grade FROM tasks WHERE deadline = ?",
                (target_date_str,),
            )
            rows = cursor.fetchall()
            if not rows:
                return []
            task_ids = [row["id"] for row in rows]
            tags_map = self._get_tags_for_tasks(conn, task_ids)
            return [self._row_to_task(row, tags_map.get(row["id"], [])) for row in rows]

    def get_tasks_in_date_range(self, start_date_str: str, end_date_str: str) -> List[Task]:
        """Получает все задачи с дедлайном в указанном диапазоне дат."""
        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT id, subject, description, deadline, effort_score, status, grade FROM tasks WHERE deadline >= ? AND deadline <= ?",
                (start_date_str, end_date_str),
            )
            rows = cursor.fetchall()
            if not rows:
                return []
            task_ids = [row["id"] for row in rows]
            tags_map = self._get_tags_for_tasks(conn, task_ids)
            return [self._row_to_task(row, tags_map.get(row["id"], [])) for row in rows]

    def rotate_local_backups(self) -> None:
        """Создает резервную копию базы данных и оставляет только MAX_BACKUPS последних бэкапов."""
        backups_dir = self.db_path.parent / "backups"
        try:
            backups_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_file = backups_dir / f"planner_backup_{timestamp}.db"

            if self.db_path.exists():
                with sqlite3.connect(backup_file) as bck_conn:
                    with self._connection() as conn:
                        conn.backup(bck_conn)

            # Ротация: оставляем только MAX_BACKUPS последних
            existing_backups = sorted(backups_dir.glob("planner_backup_*.db"), key=lambda x: x.stat().st_mtime)
            while len(existing_backups) > MAX_BACKUPS:
                oldest = existing_backups.pop(0)
                oldest.unlink()
        except OSError as e:
            logger.error(f"Ошибка при ротации бэкапов: {e}", exc_info=True)
