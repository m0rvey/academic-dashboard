import sqlite3

from src.core.logger import setup_logger

logger = setup_logger("migrations")


def run_migrations(conn: sqlite3.Connection) -> None:
    """Выполняет миграции структуры базы данных."""
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)")

    cursor = conn.execute("SELECT version FROM schema_version")
    row = cursor.fetchone()

    if not row:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        table_exists = cursor.fetchone() is not None

        if not table_exists:
            current_version = 0
        else:
            current_version = 1

        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (current_version,))
    else:
        current_version = row["version"]

    if current_version == 0:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                deadline TEXT NOT NULL,
                effort_score INTEGER NOT NULL CHECK (effort_score >= 1),
                status INTEGER NOT NULL CHECK (status IN (0, 1, 2)),
                grade INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS task_tags (
                task_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (task_id, tag_id),
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bot_users (
                chat_id INTEGER PRIMARY KEY
            )
        """)
        current_version = 4
        conn.execute("UPDATE schema_version SET version = ?", (current_version,))

    if current_version < 2:
        cursor = conn.execute("PRAGMA table_info(tasks)")
        columns = [r["name"] for r in cursor.fetchall()]

        if "is_oge" in columns:
            try:
                conn.execute("ALTER TABLE tasks DROP COLUMN is_oge")
                logger.info("Successfully dropped 'is_oge' column.")
            except sqlite3.OperationalError as e:
                logger.warning(f"Could not drop 'is_oge' column natively: {e}. It remains in the database.")

        if "grade" not in columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN grade INTEGER")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS bot_users (
                chat_id INTEGER PRIMARY KEY
            )
        """)
        current_version = 2
        conn.execute("UPDATE schema_version SET version = ?", (current_version,))

    if current_version < 3:
        # Создаем новые таблицы
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS task_tags (
                task_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (task_id, tag_id),
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)

        # Мигрируем старые теги
        cursor = conn.execute("SELECT id, tags FROM tasks")
        for row in cursor.fetchall():
            task_id = row["id"]
            old_tags_str = row["tags"]
            if old_tags_str:
                tags_list = [t.strip() for t in old_tags_str.split(",") if t.strip()]
                for t_name in tags_list:
                    conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (t_name,))
                    tag_id_cursor = conn.execute("SELECT id FROM tags WHERE name = ?", (t_name,))
                    tag_row = tag_id_cursor.fetchone()
                    if tag_row:
                        tag_id = tag_row["id"]
                        conn.execute(
                            "INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)",
                            (task_id, tag_id),
                        )

        # Пересоздаем таблицу tasks для удаления колонки tags
        conn.execute("ALTER TABLE tasks RENAME TO tasks_old")
        conn.execute("""
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                deadline TEXT NOT NULL,
                effort_score INTEGER NOT NULL CHECK (effort_score >= 1),
                status INTEGER NOT NULL CHECK (status IN (0, 1, 2)),
                grade INTEGER
            )
        """)
        conn.execute("""
            INSERT INTO tasks (id, subject, description, deadline, effort_score, status, grade)
            SELECT id, subject, description, deadline, effort_score, status, grade FROM tasks_old
        """)
        conn.execute("DROP TABLE tasks_old")

        current_version = 3
        conn.execute("UPDATE schema_version SET version = ?", (current_version,))

    if current_version < 4:
        # Recreate task_tags to fix the broken foreign key reference pointing to tasks_old
        cursor = conn.execute("SELECT task_id, tag_id FROM task_tags")
        rows = cursor.fetchall()

        conn.execute("DROP TABLE task_tags")

        conn.execute("""
            CREATE TABLE task_tags (
                task_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (task_id, tag_id),
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)

        for row in rows:
            conn.execute(
                "INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)",
                (row["task_id"], row["tag_id"]),
            )

        current_version = 4
        conn.execute("UPDATE schema_version SET version = ?", (current_version,))

    if current_version < 5:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks(deadline)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_subject ON tasks(subject)")
        current_version = 5
        conn.execute("UPDATE schema_version SET version = ?", (current_version,))

    if current_version < 6:
        cursor = conn.execute("PRAGMA table_info(bot_users)")
        cols = [r["name"] for r in cursor.fetchall()]
        if "reminder_hour" not in cols:
            conn.execute("ALTER TABLE bot_users ADD COLUMN reminder_hour INTEGER DEFAULT 9")
        current_version = 6
        conn.execute("UPDATE schema_version SET version = ?", (current_version,))

