import sqlite3
from typing import List, Optional

from src.core.config import EXAM_PRIORITY_MULTIPLIER, EXAM_TAGS
from src.core.models import Task, TaskStatus


class TaskRepository:
    """Репозиторий для управления операциями с задачами и тегами."""

    def __init__(self, db_connection) -> None:
        self.db_conn = db_connection

    def _get_tags_for_tasks(self, conn, task_ids: List[int]) -> dict:
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
        with self.db_conn.connection() as conn:
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
                    self.db_conn.notify_change()
                return task_id
            except sqlite3.Error as e:
                conn.rollback()
                raise e

    def get_all_tasks(self) -> List[Task]:
        with self.db_conn.connection() as conn:
            cursor = conn.execute("SELECT id, subject, description, deadline, effort_score, status, grade FROM tasks")
            rows = cursor.fetchall()
            if not rows:
                return []
            task_ids = [row["id"] for row in rows]
            tags_map = self._get_tags_for_tasks(conn, task_ids)
            return [self._row_to_task(row, tags_map.get(row["id"], [])) for row in rows]

    def get_active_tasks(self) -> List[Task]:
        with self.db_conn.connection() as conn:
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
        with self.db_conn.connection() as conn:
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
        with self.db_conn.connection() as conn:
            try:
                cursor = conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status.value, task_id))
                updated = cursor.rowcount > 0
                conn.commit()
                if updated:
                    self.db_conn.notify_change()
                return updated
            except sqlite3.Error as e:
                conn.rollback()
                raise e

    def update_task_grade(self, task_id: int, grade: Optional[int]) -> bool:
        with self.db_conn.connection() as conn:
            try:
                cursor = conn.execute("UPDATE tasks SET grade = ? WHERE id = ?", (grade, task_id))
                updated = cursor.rowcount > 0
                conn.commit()
                if updated:
                    self.db_conn.notify_change()
                return updated
            except sqlite3.Error as e:
                conn.rollback()
                raise e

    def update_task(self, task: Task) -> bool:
        with self.db_conn.connection() as conn:
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

                conn.execute("DELETE FROM tags WHERE id NOT IN (SELECT DISTINCT tag_id FROM task_tags)")
                conn.commit()
                if updated:
                    self.db_conn.notify_change()
                return updated
            except sqlite3.Error as e:
                conn.rollback()
                raise e

    def delete_task(self, task_id: int) -> bool:
        with self.db_conn.connection() as conn:
            try:
                cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                deleted = cursor.rowcount > 0
                if deleted:
                    conn.execute("DELETE FROM tags WHERE id NOT IN (SELECT DISTINCT tag_id FROM task_tags)")
                conn.commit()
                if deleted:
                    self.db_conn.notify_change()
                return deleted
            except sqlite3.Error as e:
                conn.rollback()
                raise e

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        with self.db_conn.connection() as conn:
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

    def get_all_tags(self) -> List[str]:
        with self.db_conn.connection() as conn:
            cursor = conn.execute("SELECT name FROM tags ORDER BY name ASC")
            return [row["name"] for row in cursor.fetchall()]

    def get_filtered_tasks(
        self,
        search_query: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        tag: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> List[Task]:
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

        with self.db_conn.connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            if not rows:
                return []
            task_ids = [row["id"] for row in rows]
            tags_map = self._get_tags_for_tasks(conn, task_ids)
            tasks = [self._row_to_task(row, tags_map.get(row["id"], [])) for row in rows]

            if search_query:
                q = search_query.lower()
                tasks = [t for t in tasks if q in t.subject.lower() or q in t.description.lower()]

            if sort_by == "subject":
                tasks.sort(key=lambda t: t.subject.lower())

            return tasks

    def get_overdue_tasks(self, today_date_str: str) -> List[Task]:
        with self.db_conn.connection() as conn:
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
        with self.db_conn.connection() as conn:
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
        with self.db_conn.connection() as conn:
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
        with self.db_conn.connection() as conn:
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
