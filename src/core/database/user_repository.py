import sqlite3
from typing import List


class UserRepository:
    """Репозиторий для управления пользователями Telegram бота."""

    def __init__(self, db_connection) -> None:
        self.db_conn = db_connection

    def register_user(self, chat_id: int) -> None:
        with self.db_conn.connection() as conn:
            try:
                conn.execute("INSERT OR IGNORE INTO bot_users (chat_id) VALUES (?)", (chat_id,))
                conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
                raise e

    def get_all_users(self) -> List[int]:
        with self.db_conn.connection() as conn:
            cursor = conn.execute("SELECT chat_id FROM bot_users")
            return [row["chat_id"] for row in cursor.fetchall()]

    def unregister_user(self, chat_id: int) -> bool:
        with self.db_conn.connection() as conn:
            try:
                cursor = conn.execute("DELETE FROM bot_users WHERE chat_id = ?", (chat_id,))
                updated = cursor.rowcount > 0
                conn.commit()
                return updated
            except sqlite3.Error as e:
                conn.rollback()
                raise e

    def get_user_reminder_hour(self, chat_id: int) -> int:
        with self.db_conn.connection() as conn:
            cursor = conn.execute("SELECT reminder_hour FROM bot_users WHERE chat_id = ?", (chat_id,))
            row = cursor.fetchone()
            if row and row["reminder_hour"] is not None:
                return int(row["reminder_hour"])
            return 9

    def set_user_reminder_hour(self, chat_id: int, hour: int) -> bool:
        with self.db_conn.connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO bot_users (chat_id, reminder_hour) VALUES (?, ?) "
                    "ON CONFLICT(chat_id) DO UPDATE SET reminder_hour = ?",
                    (chat_id, hour, hour),
                )
                conn.commit()
                return True
            except sqlite3.Error:
                conn.rollback()
                return False


    def get_users_with_reminder_hour(self, hour: int) -> List[int]:
        with self.db_conn.connection() as conn:
            cursor = conn.execute(
                "SELECT chat_id FROM bot_users WHERE COALESCE(reminder_hour, 9) = ?",
                (hour,),
            )
            return [row["chat_id"] for row in cursor.fetchall()]

