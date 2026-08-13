# 🛠️ Technical Code Documentation: Academic Dashboard

This document provides a technical overview of the architecture, components, database schemas, and synchronization mechanisms powering Academic Dashboard.

---

## 🏛️ 1. Architectural Design & Design Patterns

The codebase is organized according to **Clean Architecture** and **Domain-Driven Design (DDD)** principles:

1. **Facade Pattern**: [DatabaseManager](file:///Users/morvey/Documents/academic-dashboard/src/core/database/manager.py) acts as a unified facade delegating operations to modular repositories (`TaskRepository`, `GradeRepository`, `UserRepository`, `StatsRepository`, `BackupManager`).
2. **Repository Pattern**: Data persistence logic is separated into single-responsibility repositories under `src/core/database/`.
3. **In-Memory Reactive Cache**: [AppState](file:///Users/morvey/Documents/academic-dashboard/src/ui/state.py) caches domain tasks and metrics in memory to allow instant GUI rendering.
4. **Reactive File System Watcher**: [DBChangeHandler](file:///Users/morvey/Documents/academic-dashboard/src/ui/observers.py) listens to `.db_change` trigger file modifications using `watchdog` to refresh Flet GUI state without HTTP polling.

---

## 🗄️ 2. Database Schema & Migrations

The database is built on **SQLite3** running in **WAL mode** (`PRAGMA journal_mode = WAL;`) for high concurrency between the Telegram bot process and Flet GUI.

### Schema Structure (Migration Version 6)

```sql
-- Schema Version Tracker
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

-- Core Tasks Table
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    description TEXT NOT NULL,
    deadline TEXT NOT NULL,
    effort_score INTEGER NOT NULL CHECK (effort_score >= 1),
    status INTEGER NOT NULL CHECK (status IN (0, 1, 2)), -- 0: TODO, 1: DOING, 2: DONE
    grade INTEGER
);

-- Tags & Junction Table
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS task_tags (
    task_id INTEGER,
    tag_id INTEGER,
    PRIMARY KEY (task_id, tag_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Telegram Bot Authorized Users & Settings
CREATE TABLE IF NOT EXISTS bot_users (
    chat_id INTEGER PRIMARY KEY,
    reminder_hour INTEGER DEFAULT 9
);

-- Indexes for Fast Querying
CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks(deadline);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_subject ON tasks(subject);
```

---

## 🔄 3. APFS Real-Time Synchronization Observer

To handle macOS APFS `mtime` file caching, database changes invoke [notify_change()](file:///Users/morvey/Documents/academic-dashboard/src/core/database/connection.py#L19-L28):

```python
def notify_change(self) -> None:
    """Updates the trigger file timestamp to fire watchdog file-system events."""
    try:
        import time

        trigger_path = self.db_path.parent / ".db_change"
        trigger_path.parent.mkdir(parents=True, exist_ok=True)
        with open(trigger_path, "w", encoding="utf-8") as f:
            f.write(str(time.time()))
    except OSError as e:
        logger.warning(f"Error in notify_change: {e}")
```

---

## ⌨️ 4. Flet GUI Keyboard Shortcuts

Keyboard navigation is hooked into [page.on_keyboard_event](file:///Users/morvey/Documents/academic-dashboard/src/ui/views/main_view.py#L411-L442):

| Shortcut (macOS / Win) | Action | Handler Function |
| :--- | :--- | :--- |
| `Cmd + N` / `Ctrl + N` | Open Add Task Modal | `open_add_dialog(None)` |
| `Cmd + F` / `Ctrl + F` | Focus Search Field | `search_field.focus()` |
| `Cmd + R` / `Ctrl + R` | Force Data Refresh | `trigger_data_update()` |
| `Cmd + T` / `Ctrl + T` | Toggle Dark / Light Theme | `toggle_theme(None)` |

---

## 🤖 5. Telegram Bot Command Routers

Handlers in `src/bot/handlers/` use Aiogram 3 routers:

- **[commands.py](file:///Users/morvey/Documents/academic-dashboard/src/bot/handlers/commands.py)**: `/start`, `/help`, `/cancel`, `/load`, `/backup`, `/settings` (interactive time picker).
- **[tasks.py](file:///Users/morvey/Documents/academic-dashboard/src/bot/handlers/tasks.py)**: `/list`, `/add`, `/done`, NLP Russian speech parser, and inline callback queries (`task_doing_`, `task_todo_`, `complete_`, `task_del_`, `refresh_list`, `add_task_start`).
- **[dashboards.py](file:///Users/morvey/Documents/academic-dashboard/src/bot/handlers/dashboards.py)**: `/stats` (KPI dashboard) and `/grades` (GPA tracker).
