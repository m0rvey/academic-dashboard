import asyncio
import atexit
import signal
import sys
import warnings
from datetime import date, datetime
from typing import Optional

from src.core.config import DAILY_LOAD_LIMIT, DB_PATH, MAX_EFFORT, MIN_EFFORT
from src.core.database import DatabaseManager
from src.core.interfaces import IDatabaseManager
from src.core.logic import calculate_priority, check_daily_load, get_daily_load
from src.core.models import Task, TaskStatus, get_clean_date
from src.ui.views import run_gui

# Глобальная политика циклов событий для предотвращения ошибок "There is no current event loop" в фоновых потоках
try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=DeprecationWarning)

        class GlobalEventLoopPolicy(asyncio.DefaultEventLoopPolicy):
            def get_event_loop(self):
                try:
                    loop = super().get_event_loop()
                    if loop is not None and not loop.is_closed():
                        self._loop = loop
                    return loop
                except RuntimeError:
                    if not hasattr(self, "_loop") or self._loop is None or self._loop.is_closed():
                        self._loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(self._loop)
                    return self._loop

        asyncio.set_event_loop_policy(GlobalEventLoopPolicy())
except Exception:
    pass



def setup_signal_handlers() -> None:
    """Перехватывает сигналы завершения (SIGINT, SIGTERM, SIGHUP) для корректного закрытия бота и Flet при закрытии терминала VS Code."""
    import os

    def _handle_exit(signum=None, frame=None):
        try:
            from bot import stop_bot_in_thread
            stop_bot_in_thread()
        except Exception:
            pass
        os._exit(0)

    try:
        from bot import stop_bot_in_thread
        atexit.register(stop_bot_in_thread)
    except Exception:
        pass

    for sig in (signal.SIGINT, signal.SIGTERM, getattr(signal, "SIGHUP", None)):
        if sig is not None:
            try:
                signal.signal(sig, _handle_exit)
            except (ValueError, OSError):
                pass


setup_signal_handlers()



def print_menu() -> None:
    """Выводит интерактивное CLI-меню в консоль."""
    print("\n=== Academic Dashboard ===")
    print("1. Добавить задачу")
    print("2. Показать список задач (по приоритету)")
    print("3. Показать текущую дневную нагрузку")
    print("4. Изменить статус задачи")
    print("5. Выход")
    print("==========================")


def input_date(prompt: str) -> Optional[str]:
    """Безопасно считывает дату от пользователя через datetime, обрабатывая ошибки ввода.
    Возвращает None при вводе 'отмена' или 'cancel'.
    """
    while True:
        user_input = input(prompt).strip()
        if user_input.lower() in ("отмена", "cancel"):
            return None
        try:
            # Проверяем корректность формата YYYY-MM-DD
            parsed_date = datetime.strptime(user_input, "%Y-%m-%d").date()
            return parsed_date.isoformat()
        except ValueError:
            print(
                "❌ Неверный формат даты. Пожалуйста, введите дату в формате ГГГГ-ММ-ДД (например, 2026-05-29) или 'отмена'."
            )


def input_int(prompt: str, min_val: int = 1, max_val: Optional[int] = None) -> Optional[int]:
    """Запрашивает корректное целое число от пользователя.
    Возвращает None при вводе 'отмена' или 'cancel'.
    """
    while True:
        user_input = input(prompt).strip()
        if user_input.lower() in ("отмена", "cancel"):
            return None
        try:
            val = int(user_input)
            if val < min_val:
                print(f"❌ Число должно быть не меньше {min_val}.")
                continue
            if max_val is not None and val > max_val:
                print(f"❌ Число должно быть не больше {max_val}.")
                continue
            return val
        except ValueError:
            print("❌ Пожалуйста, введите корректное целое число или 'отмена'.")


def check_and_warn_load(db: IDatabaseManager, target_date: str) -> None:
    """Проверяет дневную нагрузку и выводит предупреждение."""
    total_load, is_overloaded = check_daily_load(db.get_all_tasks(), target_date)
    if is_overloaded:
        clean_target = get_clean_date(target_date)
        print(
            f"\n⚠️ ПРЕДУПРЕЖДЕНИЕ: Дневная нагрузка на {clean_target} превышает лимит ({DAILY_LOAD_LIMIT} ед.)! Текущая нагрузка: {total_load} ед."
        )


def _run_cli() -> None:
    # Создаем менеджер БД и инициализируем таблицы
    db = DatabaseManager(DB_PATH)
    db.init_db()

    while True:
        print_menu()
        choice = input("Выберите действие (1-5): ").strip()

        if choice == "1":
            print("\n--- Добавление новой задачи (введите 'отмена' для возврата) ---")
            subject = input("Предмет: ").strip()
            if subject.lower() in ("отмена", "cancel"):
                print("❌ Добавление задачи отменено.")
                continue
            while not subject:
                print("❌ Название предмета не может быть пустым.")
                subject = input("Предмет: ").strip()
                if subject.lower() in ("отмена", "cancel"):
                    break
            if subject.lower() in ("отмена", "cancel"):
                print("❌ Добавление задачи отменено.")
                continue

            description = input("Описание: ").strip()
            if description.lower() in ("отмена", "cancel"):
                print("❌ Добавление задачи отменено.")
                continue
            while not description:
                print("❌ Описание не может быть пустым.")
                description = input("Описание: ").strip()
                if description.lower() in ("отмена", "cancel"):
                    break
            if description.lower() in ("отмена", "cancel"):
                print("❌ Добавление задачи отменено.")
                continue

            deadline = input_date("Дедлайн (ГГГГ-ММ-ДД): ")
            if deadline is None:
                print("❌ Добавление задачи отменено.")
                continue

            effort_score = input_int(
                f"Нагрузка (effort score, от {MIN_EFFORT} до {MAX_EFFORT}): ", min_val=MIN_EFFORT, max_val=MAX_EFFORT
            )
            if effort_score is None:
                print("❌ Добавление задачи отменено.")
                continue

            tags_input = input("Теги (через запятую, например: ОГЭ, Домашка): ").strip()
            if tags_input.lower() in ("отмена", "cancel"):
                print("❌ Добавление задачи отменено.")
                continue
            tags = [t.strip() for t in tags_input.split(",") if t.strip()]

            new_task = Task(
                subject=subject,
                description=description,
                deadline=deadline,
                effort_score=effort_score,
                tags=tags,
                status=TaskStatus.TODO,
            )

            task_id = db.add_task(new_task)
            print(f"✅ Задача успешно добавлена с ID {task_id}!")

            # Проверяем нагрузку на дату дедлайна новой задачи
            check_and_warn_load(db, deadline)

        elif choice == "2":
            print("\n--- Список задач (отсортирован по приоритету) ---")
            tasks = db.get_all_tasks()
            if not tasks:
                print("Список задач пуст.")
                continue

            # Сортируем задачи по приоритету (по убыванию)
            sorted_tasks = sorted(tasks, key=calculate_priority, reverse=True)

            status_labels = {TaskStatus.TODO: "TODO", TaskStatus.DOING: "DOING", TaskStatus.DONE: "DONE"}

            for task in sorted_tasks:
                priority = calculate_priority(task)
                tags_str = f" [{', '.join(task.tags)}]" if task.tags else ""
                print(
                    f"ID: {task.id} | {task.subject}{tags_str} | Приоритет: {priority:.2f}\n"
                    f"  Статус: {status_labels[task.status]} | Сложность: {task.effort_score} | Дедлайн: {task.deadline}\n"
                    f"  Описание: {task.description}\n"
                )

        elif choice == "3":
            print("\n--- Проверка текущей дневной нагрузки ---")
            today_str = date.today().isoformat()
            all_tasks = db.get_all_tasks()

            # Фильтруем задачи на сегодня
            today_tasks = [task for task in all_tasks if get_clean_date(task.deadline) == today_str]
            total_load = get_daily_load(today_tasks)

            print(f"Текущая нагрузка на сегодня ({today_str}): {total_load} ед.")
            if total_load > DAILY_LOAD_LIMIT:
                print(
                    f"⚠️ ПРЕДУПРЕЖДЕНИЕ: Дневная нагрузка превышает лимит ({DAILY_LOAD_LIMIT} ед.)! Перегрузка на {total_load - DAILY_LOAD_LIMIT} ед."
                )
            else:
                print(f"Нагрузка находится в пределах нормы (<= {DAILY_LOAD_LIMIT} ед.).")

        elif choice == "4":
            print("\n--- Изменение статуса задачи ---")
            task_id = input_int("Введите ID задачи: ", min_val=1)
            if task_id is None:
                print("❌ Изменение статуса отменено.")
                continue

            # Проверяем, существует ли задача с таким ID
            all_tasks = db.get_all_tasks()
            task_exists = any(task.id == task_id for task in all_tasks)
            if not task_exists:
                print(f"❌ Задача с ID {task_id} не была найдена.")
                continue

            print("Доступные статусы:")
            print("0 - TODO")
            print("1 - DOING")
            print("2 - DONE")

            while True:
                status_input = input("Выберите новый статус (0, 1, 2): ").strip()
                if status_input in ("0", "1", "2"):
                    new_status = TaskStatus(int(status_input))
                    break
                print("❌ Неверный статус. Пожалуйста, введите 0, 1 или 2.")

            if db.update_task_status(task_id, new_status):
                print(f"✅ Статус задачи с ID {task_id} успешно изменен!")
            else:
                print("❌ Не удалось обновить статус задачи.")

        elif choice == "5":
            print("Выход из программы. Удачи в учебе!")
            break

        else:
            print("❌ Неверный пункт меню. Попробуйте еще раз.")


def main() -> None:
    if "--cli" in sys.argv:
        try:
            _run_cli()
        except KeyboardInterrupt:
            print("\n  Выход...")
            sys.exit(0)
    else:
        db = DatabaseManager(DB_PATH)
        db.init_db()
        run_gui(db)



if __name__ == "__main__":
    main()
