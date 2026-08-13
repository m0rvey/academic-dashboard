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
