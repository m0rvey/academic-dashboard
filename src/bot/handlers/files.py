import json
import sqlite3
import uuid
from pathlib import Path

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message

from src.bot.dependencies import ADMIN_USERS, bot, logger
from src.bot.state import BotState
from src.core.database import DatabaseManager

router = Router()


@router.message(F.document)
async def handle_document_restore(message: Message, db: DatabaseManager, app_state: BotState):
    db.register_user(message.chat.id)
    if message.from_user.id not in ADMIN_USERS:
        await message.answer("⛔ У вас нет прав на загрузку резервных копий или импорт данных.")
        return
    document = message.document
    file_name = document.file_name

    if not file_name:
        await message.answer("❌ Не удалось получить имя файла.")
        return

    safe_base_name = Path(file_name).name
    ext = Path(safe_base_name).suffix.lower()
    if ext not in (".db", ".json"):
        await message.answer(
            "❌ Поддерживаются только файлы резервных копии `.db` (SQLite) или файлы экспорта задач `.json`."
        )
        return

    temp_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file_path = temp_dir / f"restore_{uuid.uuid4().hex}_{safe_base_name}"

    try:
        file_info = await bot.get_file(document.file_id)
        await bot.download_file(file_info.file_path, destination=temp_file_path)

        if ext == ".db":
            try:
                conn = sqlite3.connect(temp_file_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
                table_exists = cursor.fetchone() is not None
                if not table_exists:
                    conn.close()
                    raise ValueError("В базе данных отсутствует таблица 'tasks'.")

                cursor = conn.execute("PRAGMA table_info(tasks)")
                columns = {row["name"] for row in cursor.fetchall()}
                required = {"subject", "description", "deadline", "effort_score"}
                if not required.issubset(columns):
                    conn.close()
                    raise ValueError(
                        f"Таблица 'tasks' имеет неверную структуру. Отсутствуют обязательные колонки: {required - columns}"
                    )

                conn.close()
            except (sqlite3.Error, ValueError) as e:
                await message.answer(f"❌ Ошибка валидации базы данных: {e}")
                return

            db.rotate_local_backups()

            try:
                source = sqlite3.connect(temp_file_path)
                with db._connection() as dst:
                    source.backup(dst)
                source.close()
                db._notify_change()
                app_state.invalidate()
            except sqlite3.Error as e:
                await message.answer(f"❌ Ошибка при восстановлении базы данных: {e}")
                return

            await message.answer(
                "📦 *База данных успешно восстановлена!*\n"
                "Предыдущая версия сохранена в локальной папке `data/backups/`. "
                "Интерфейс приложения обновится автоматически.",
                parse_mode="Markdown",
            )

        elif ext == ".json":
            try:
                db.import_from_json(temp_file_path)
                db._notify_change()
                app_state.invalidate()
                await message.answer(
                    "📝 *Задачи из JSON успешно импортированы!*\n"
                    "Все новые задачи добавлены в текущую базу данных. "
                    "Интерфейс приложения обновится автоматически.",
                    parse_mode="Markdown",
                )
            except (json.JSONDecodeError, FileNotFoundError, ValueError, KeyError) as e:
                await message.answer(f"❌ Ошибка при импорте из JSON: {e}")

    except (TelegramAPIError, OSError, ValueError) as e:
        await message.answer(f"❌ Произошла ошибка при обработке файла: {e}")
    finally:
        if temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except OSError as e:
                logger.warning(f"Error removing temp file: {e}")
