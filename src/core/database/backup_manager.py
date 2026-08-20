import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

from src.core.config import MAX_BACKUPS
from src.core.logger import setup_logger
from src.core.models import Task, TaskStatus

logger = setup_logger("backup_manager")


class BackupManager:
    """Управление экспортом/импортом данных в JSON и локальной ротацией бэкапов."""

    def __init__(self, db_connection, task_repository, notify_callback=None) -> None:
        self.db_conn = db_connection
        self.task_repo = task_repository
        self.notify_callback = notify_callback or db_connection.notify_change

    def export_to_json(self, filepath: str) -> None:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        tasks = self.task_repo.get_all_tasks()
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
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Файл бэкапа не найден по пути: {filepath}")

        MAX_IMPORT_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
        if path.stat().st_size > MAX_IMPORT_FILE_SIZE:
            raise ValueError(f"Размер файла превышает допустимый лимит ({MAX_IMPORT_FILE_SIZE} байт)")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("Неверный формат данных JSON: ожидается список задач.")

        MAX_IMPORT_TASKS = 5000
        data = data[:MAX_IMPORT_TASKS]

        imported_any = False
        for item in data:
            if not isinstance(item, dict):
                continue
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

            raw_subject = str(item.get("subject", "")).strip()[:255]
            raw_description = str(item.get("description", "")).strip()[:2000]
            raw_deadline = str(item.get("deadline", "")).strip()[:20]

            raw_tags = item.get("tags", [])
            if not isinstance(raw_tags, list):
                raw_tags = []
            sanitized_tags = [str(t).strip()[:50] for t in raw_tags if str(t).strip()][:30]

            try:
                effort = max(1, min(10, int(item.get("effort_score", 1))))
            except (ValueError, TypeError):
                effort = 1

            task = Task(
                subject=raw_subject if raw_subject else "Без предмета",
                description=raw_description if raw_description else "Без описания",
                deadline=raw_deadline if raw_deadline else date.today().isoformat(),
                effort_score=effort,
                tags=sanitized_tags,
                status=status,
                grade=grade_val,
            )
            self.task_repo.add_task(task, notify=False)
            imported_any = True

        if imported_any:
            self.notify_callback()

    def rotate_local_backups(self) -> None:
        backups_dir = self.db_conn.db_path.parent / "backups"
        try:
            backups_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_file = backups_dir / f"planner_backup_{timestamp}.db"

            if self.db_conn.db_path.exists():
                with sqlite3.connect(backup_file) as bck_conn:
                    with self.db_conn.connection() as conn:
                        conn.backup(bck_conn)

            existing_backups = sorted(backups_dir.glob("planner_backup_*.db"), key=lambda x: x.stat().st_mtime)
            while len(existing_backups) > MAX_BACKUPS:
                oldest = existing_backups.pop(0)
                oldest.unlink()
        except OSError as e:
            logger.error(f"Ошибка при ротации бэкапов: {e}", exc_info=True)
