import asyncio
import json
import os
import tempfile
import threading
from datetime import date

import flet as ft
from watchdog.observers import Observer

from src.core.config import DAILY_LOAD_LIMIT
from src.core.interfaces import IDatabaseManager
from src.core.logger import setup_logger
from src.ui.components.notifications import send_desktop_notifications
from src.ui.constants import BG_CARD, FILTER_ALL, FILTER_ALL_TAGS, SORT_PRIORITY
from src.ui.dialogs.add_edit_dialog import create_add_edit_dialog
from src.ui.dialogs.delete_dialog import create_delete_dialog
from src.ui.observers import DBChangeHandler
from src.ui.state import AppState
from src.ui.tabs.calendar_tab import create_calendar_tab
from src.ui.tabs.grades_tab import create_grades_tab, update_grades_view
from src.ui.tabs.stats_tab import create_stats_tab, update_kpi_cards, update_stats_charts
from src.ui.tabs.tasks_tab import create_tasks_tab, update_task_list

logger = setup_logger("views")


def run_gui(db: IDatabaseManager) -> None:
    """Запускает графический интерфейс приложения."""
    db.rotate_local_backups()

    import sys
    if "pytest" not in sys.modules:
        from bot import start_bot_in_thread
        start_bot_in_thread()

    async def main(page: ft.Page) -> None:
        from src.core.config import ENV_PATH
        import os
        from dotenv import load_dotenv

        load_dotenv(dotenv_path=ENV_PATH, override=True)
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        allowed_users = os.getenv("TELEGRAM_ALLOWED_USERS")

        setup_needed = (
            not token
            or token in ("YOUR_TELEGRAM_BOT_TOKEN_HERE", "your_token_here", "")
            or not allowed_users
        )

        def show_dashboard():
            page.clean()
            page.title = "Academic Dashboard"
            page.scroll = ft.ScrollMode.ADAPTIVE
            page.padding = 20
            page.horizontal_alignment = ft.CrossAxisAlignment.START
            page.vertical_alignment = ft.MainAxisAlignment.START

            # Load session configuration
            config_path = db.db_path.parent / "session_config.json"
            session_config = {
                "theme_mode": "dark",
                "filter_status": FILTER_ALL,
                "filter_tag": FILTER_ALL_TAGS,
                "sort_by": SORT_PRIORITY,
            }
            if config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        session_config.update(json.load(f))
                except Exception as ex:
                    logger.warning(f"Error loading session config: {ex}")

            page.theme_mode = ft.ThemeMode.DARK if session_config["theme_mode"] == "dark" else ft.ThemeMode.LIGHT

            # Initialize global app state cache
            app_state = AppState(db)
            app_state.reload()

            # State tracking variables
            notified_task_ids = set()
            active_notification_tasks = set()
            last_notification_date_ref = [date.today()]

            def _on_notification_done(task_ref):
                active_notification_tasks.discard(task_ref)
                try:
                    task_ref.result()
                except Exception as ex:
                    logger.error(f"Error in notify_mac background task: {ex}", exc_info=True)

            config_write_lock = threading.Lock()

            def save_session_config():
                with config_write_lock:
                    session_config["theme_mode"] = "dark" if page.theme_mode == ft.ThemeMode.DARK else "light"
                    session_config["filter_status"] = filter_status.value
                    session_config["filter_tag"] = filter_tag.value
                    session_config["sort_by"] = sort_dropdown.value
                    try:
                        config_path.parent.mkdir(parents=True, exist_ok=True)
                        temp_fd, temp_path = tempfile.mkstemp(
                            dir=str(config_path.parent),
                            prefix="session_config_",
                            suffix=".tmp",
                        )
                        try:
                            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                                json.dump(session_config, f, ensure_ascii=False, indent=2)
                            os.replace(temp_path, config_path)
                        except Exception as ex:
                            if os.path.exists(temp_path):
                                os.unlink(temp_path)
                            raise ex
                    except Exception as ex:
                        logger.warning(f"Error saving session config: {ex}")

            def toggle_theme(e):
                page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
                theme_icon.icon = ft.Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.DARK else ft.Icons.LIGHT_MODE
                theme_icon.icon_color = ft.Colors.BLUE_GREY if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.AMBER
                save_session_config()
                page.update()

            def show_snack(msg: str):
                page.open(ft.SnackBar(ft.Text(msg)))

            def export_data(e):
                path = db.db_path.parent / "academic_backup.json"
                db.export_to_json(str(path))
                show_snack(f"✅ Экспортировано в {path.name}")

            def import_data(e):
                path = db.db_path.parent / "academic_backup.json"
                if path.exists():
                    try:
                        db.import_from_json(str(path))
                        show_snack("✅ Данные успешно импортированы!")
                        trigger_data_update()
                    except Exception as exx:
                        show_snack(f"❌ Ошибка импорта: {str(exx)}")
                else:
                    show_snack(f"❌ Файл бэкапа не найден по пути {path.name}!")

            def trigger_data_update():
                app_state.reload()
                _update_load_indicator()
                # Always run notifications check
                send_desktop_notifications(
                    db,
                    notified_task_ids,
                    active_notification_tasks,
                    _on_notification_done,
                    last_notification_date_ref,
                )
                refresh_active_tab()

            # Initialize Modal Dialogs
            add_dialog, open_add_dialog, open_edit_dialog = create_add_edit_dialog(
                page, db, show_snack, lambda: trigger_data_update()
            )
            delete_confirm_dialog, open_delete_confirm = create_delete_dialog(
                page, db, show_snack, lambda: trigger_data_update()
            )

            # Initialize Tabs
            (
                tasks_view,
                search_field,
                filter_status,
                filter_tag,
                sort_dropdown,
                task_list,
            ) = create_tasks_tab(session_config, save_session_config, lambda: trigger_data_update())
            (
                stats_view,
                kpi_row,
                stats_chart,
                tag_load_list,
                legend_wrap,
                productivity_chart,
                period_dropdown,
            ) = create_stats_tab()
            period_dropdown.on_change = lambda e: trigger_data_update()

            (
                grades_view,
                grades_placeholder,
                grades_layout_container,
                grades_kpi_row,
                subject_grades_list,
                grades_chart,
            ) = create_grades_tab(page, db)
            calendar_view, update_calendar_grid = create_calendar_tab(db, page)

            # Header bar setup
            theme_icon = ft.IconButton(
                icon=(ft.Icons.LIGHT_MODE if page.theme_mode == ft.ThemeMode.DARK else ft.Icons.DARK_MODE),
                icon_color=(ft.Colors.AMBER if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.BLUE_GREY),
                on_click=toggle_theme,
                tooltip="Сменить тему",
            )
            header = ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.DASHBOARD_ROUNDED,
                                color=ft.Colors.LIGHT_BLUE_200,
                                size=28,
                            ),
                            ft.Text(
                                "Академический дашборд",
                                theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.LIGHT_BLUE_200,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.DOWNLOAD_ROUNDED,
                                icon_color=ft.Colors.LIGHT_BLUE_200,
                                on_click=import_data,
                                tooltip="Импорт из JSON",
                            ),
                            ft.IconButton(
                                icon=ft.Icons.UPLOAD_ROUNDED,
                                icon_color=ft.Colors.LIGHT_BLUE_200,
                                on_click=export_data,
                                tooltip="Экспорт в JSON",
                            ),
                            theme_icon,
                        ],
                        spacing=5,
                    ),
                ],
            )

            # Daily Workload indicators setup
            load_label = ft.Text(
                f"Дневная нагрузка на сегодня: 0 / {DAILY_LOAD_LIMIT}",
                size=15,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.LIGHT_BLUE_100,
            )
            load_progress = ft.ProgressBar(
                value=0.0,
                color=ft.Colors.GREEN_ACCENT,
                bgcolor=ft.Colors.GREY_800,
                height=8,
                border_radius=4,
            )
            warning_banner = ft.Text(
                "",
                color=ft.Colors.RED_ACCENT,
                size=13,
                weight=ft.FontWeight.BOLD,
                visible=False,
            )
            load_container = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.AUTO_AWESOME, size=16, color=ft.Colors.AMBER),
                                load_label,
                            ],
                            spacing=6,
                        ),
                        load_progress,
                        warning_banner,
                    ],
                    spacing=8,
                ),
                padding=15,
                border_radius=12,
                bgcolor=BG_CARD,
                border=ft.border.all(1, ft.Colors.GREY_800),
            )

            tabs = ft.Tabs(
                selected_index=0,
                animation_duration=250,
                on_change=lambda e: refresh_active_tab(),
                tabs=[
                    ft.Tab(text="Задачи", icon=ft.Icons.LIST_ROUNDED, content=tasks_view),
                    ft.Tab(
                        text="Статистика",
                        icon=ft.Icons.PIE_CHART_ROUNDED,
                        content=stats_view,
                    ),
                    ft.Tab(
                        text="Успеваемость",
                        icon=ft.Icons.SCHOOL_ROUNDED,
                        content=grades_view,
                    ),
                    ft.Tab(
                        text="Календарь",
                        icon=ft.Icons.CALENDAR_MONTH_ROUNDED,
                        content=calendar_view,
                    ),
                ],
                expand=True,
            )

            fab = ft.FloatingActionButton(
                icon=ft.Icons.ADD_ROUNDED,
                bgcolor=ft.Colors.LIGHT_BLUE_600,
                on_click=open_add_dialog,
                tooltip="Добавить задачу",
            )

            def _update_load_indicator():
                today_str = date.today().isoformat()
                try:
                    load, is_overloaded = db.get_daily_load_for_date(today_str)
                except Exception as ex:
                    logger.warning(f"Error getting daily load: {ex}")
                    load, is_overloaded = 0, False

                load_progress.value = min(1.0, load / DAILY_LOAD_LIMIT)
                if is_overloaded:
                    load_progress.color = ft.Colors.RED_ACCENT
                    warning_banner.value = f"⚠️ ВНИМАНИЕ: Превышена дневная нагрузка! Текущая: {load} из {DAILY_LOAD_LIMIT}."
                    warning_banner.visible = True
                else:
                    load_progress.color = ft.Colors.GREEN_ACCENT
                    warning_banner.visible = False
                load_label.value = f"Дневная нагрузка на сегодня: {load} / {DAILY_LOAD_LIMIT}"

            def refresh_active_tab(e=None):
                idx = tabs.selected_index
                if app_state.is_dirty(idx):
                    if idx == 0:
                        try:
                            update_task_list(
                                db,
                                search_field,
                                filter_status,
                                filter_tag,
                                sort_dropdown,
                                task_list,
                                trigger_data_update,
                                open_edit_dialog,
                                open_delete_confirm,
                            )
                        except Exception as ex:
                            logger.error(f"Error in update_task_list: {ex}", exc_info=True)
                    elif idx == 1:
                        try:
                            update_kpi_cards(db, kpi_row, period_dropdown)
                            update_stats_charts(
                                db,
                                stats_chart,
                                legend_wrap,
                                productivity_chart,
                                tag_load_list,
                                period_dropdown,
                                app_state.get_subject_color,
                            )
                        except Exception as ex:
                            logger.warning(f"Error in stats tab: {ex}")
                    elif idx == 2:
                        try:
                            update_grades_view(
                                db,
                                grades_placeholder,
                                grades_layout_container,
                                grades_kpi_row,
                                subject_grades_list,
                                grades_chart,
                            )
                        except Exception as ex:
                            logger.warning(f"Error in grades tab: {ex}")
                    elif idx == 3:
                        try:
                            update_calendar_grid()
                        except Exception as ex:
                            logger.warning(f"Error in calendar tab: {ex}")

                    app_state.mark_clean(idx)
                page.update()

            page.add(ft.Column([header, load_container, tabs], expand=True, spacing=15))
            page.floating_action_button = fab

            # Initial trigger to populate the UI
            trigger_data_update()

            # Database Observer (watchdog)
            loop = asyncio.get_running_loop()

            _refresh_lock = asyncio.Lock()
            refresh_state = {"handle": None}

            def _schedule_refresh():
                if refresh_state["handle"] is not None:
                    refresh_state["handle"].cancel()
                refresh_state["handle"] = loop.call_later(0.3, lambda: page.run_task(_safe_refresh))

            async def _safe_refresh():
                if _refresh_lock.locked():
                    return
                async with _refresh_lock:
                    try:
                        trigger_data_update()
                    except Exception as ex:
                        logger.error(f"Error in _safe_refresh: {ex}")

            observer = Observer()
            handler = DBChangeHandler(_schedule_refresh)
            observer.schedule(handler, path=str(db.db_path.parent), recursive=False)
            observer.start()

            def cleanup(e):
                observer.stop()
                observer.join()
                db.rotate_local_backups()
                try:
                    from bot import stop_bot_in_thread
                    stop_bot_in_thread()
                except Exception as ex:
                    logger.error(f"Error stopping bot on GUI exit: {ex}")

            page.on_disconnect = cleanup
            page.update()

        def show_setup_view():
            page.clean()
            page.title = "Настройка Academic Dashboard"
            page.scroll = ft.ScrollMode.ADAPTIVE
            page.padding = 40
            page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
            page.vertical_alignment = ft.MainAxisAlignment.CENTER

            token_input = ft.TextField(
                label="Токен Telegram-бота (от @BotFather)",
                password=True,
                can_reveal_password=True,
                border_color=ft.Colors.LIGHT_BLUE_400,
                border_radius=10,
                width=450,
            )
            chat_id_input = ft.TextField(
                label="Ваш Telegram Chat ID (от @userinfobot)",
                border_color=ft.Colors.LIGHT_BLUE_400,
                border_radius=10,
                width=450,
            )

            def save_credentials(e):
                token_val = token_input.value.strip()
                chat_id_val = chat_id_input.value.strip()

                if not token_val or not chat_id_val:
                    page.open(ft.SnackBar(ft.Text("❌ Пожалуйста, заполните оба поля!")))
                    return

                try:
                    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
                    with open(ENV_PATH, "w", encoding="utf-8") as f:
                        f.write(f"TELEGRAM_BOT_TOKEN={token_val}\n")
                        f.write(f"TELEGRAM_ALLOWED_USERS={chat_id_val}\n")
                        f.write(f"TELEGRAM_ADMIN_USERS={chat_id_val}\n")

                    from dotenv import load_dotenv
                    load_dotenv(dotenv_path=ENV_PATH, override=True)

                    import sys
                    import importlib

                    # Перезагружаем все модули бота в правильном порядке, чтобы подхватить новые настройки
                    modules_to_reload = [
                        "src.bot.dependencies",
                        "src.bot.middlewares.auth",
                        "src.bot.middlewares.dependencies",
                        "src.bot.middlewares.throttling",
                        "src.bot.handlers.commands",
                        "src.bot.handlers.dashboards",
                        "src.bot.handlers.files",
                        "src.bot.handlers.tasks",
                        "src.bot.scheduler",
                        "bot"
                    ]

                    for mod_name in modules_to_reload:
                        if mod_name in sys.modules:
                            importlib.reload(sys.modules[mod_name])

                    from bot import start_bot_in_thread
                    start_bot_in_thread()

                    page.open(ft.SnackBar(ft.Text("✅ Настройки успешно сохранены! Запуск бота...")))
                    show_dashboard()
                except Exception as ex:
                    page.open(ft.SnackBar(ft.Text(f"❌ Ошибка сохранения: {ex}")))

            setup_card = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.AUTO_STORIES_ROUNDED, size=60, color=ft.Colors.LIGHT_BLUE_200),
                        ft.Text(
                            "Academic Dashboard",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.LIGHT_BLUE_200,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Добро пожаловать! Пожалуйста, укажите токен Telegram-бота и ваш Telegram Chat ID, чтобы начать работу с приложением.",
                            size=14,
                            color=ft.Colors.GREY_400,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Divider(color=ft.Colors.GREY_800, height=20),
                        token_input,
                        chat_id_input,
                        ft.Container(height=10),
                        ft.ElevatedButton(
                            text="Сохранить и запустить",
                            on_click=save_credentials,
                            bgcolor=ft.Colors.LIGHT_BLUE_600,
                            color=ft.Colors.WHITE,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=10),
                            ),
                            width=450,
                            height=45,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                ),
                bgcolor=BG_CARD,
                padding=40,
                border_radius=16,
                border=ft.border.all(1, ft.Colors.GREY_800),
                width=500,
            )

            page.add(
                ft.Container(
                    content=setup_card,
                    alignment=ft.alignment.center,
                    expand=True,
                )
            )
            page.update()

        # Выбираем режим при старте
        if setup_needed:
            show_setup_view()
        else:
            show_dashboard()

    ft.app(target=main)
