import json
import os
import tempfile
import threading
from datetime import date

import flet as ft
from watchdog.observers import Observer

from src.core.interfaces import IDatabaseManager
from src.core.logger import setup_logger
from src.ui.components.notifications import send_desktop_notifications
from src.ui.constants import FILTER_ALL, FILTER_ALL_TAGS, SORT_PRIORITY
from src.ui.dialogs.add_edit_dialog import create_add_edit_dialog
from src.ui.dialogs.delete_dialog import create_delete_dialog
from src.ui.observers import DBChangeHandler
from src.ui.state import AppState
from src.ui.tabs.calendar_tab import create_calendar_tab
from src.ui.tabs.grades_tab import create_grades_tab, update_grades_view
from src.ui.tabs.stats_tab import create_stats_tab, update_kpi_cards, update_stats_charts
from src.ui.tabs.tasks_tab import create_tasks_tab, update_task_list
from src.ui.views.debug_console import show_debug_console
from src.ui.views.workload_indicator import create_workload_indicator

logger = setup_logger("views")


def run_gui(db: IDatabaseManager) -> None:
    """Запускает графический интерфейс приложения."""
    db.rotate_local_backups()

    import sys
    if "pytest" not in sys.modules:
        from bot import start_bot_in_thread
        start_bot_in_thread()

    def main(page: ft.Page) -> None:
        from dotenv import load_dotenv

        from src.core.config import ENV_PATH

        if not ENV_PATH.exists():
            example_path = ENV_PATH.parent / ".env.example"
            if example_path.exists():
                try:
                    import shutil
                    shutil.copy(example_path, ENV_PATH)
                    logger.info("Файл .env не найден. Создан шаблон .env из .env.example.")
                except Exception as ex:
                    logger.warning(f"Не удалось скопировать .env.example в .env: {ex}")

        load_dotenv(dotenv_path=ENV_PATH, override=True)


        def _open_debug_console(e=None):
            show_debug_console(page)

        def show_dashboard():
            page.clean()
            page.title = "Academic Dashboard"
            page.scroll = ft.ScrollMode.ADAPTIVE
            page.padding = 20
            page.horizontal_alignment = ft.CrossAxisAlignment.START
            page.vertical_alignment = ft.MainAxisAlignment.START

            # Bot status UI elements
            bot_status_dot = ft.Icon(ft.Icons.CIRCLE, color=ft.Colors.RED_ACCENT, size=10)
            bot_status_text = ft.Text("Бот: Неактивен", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_300)

            bot_status_badge = ft.Container(
                content=ft.Row(
                    [
                        bot_status_dot,
                        bot_status_text,
                    ],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                border_radius=8,
                bgcolor=ft.Colors.GREY_900,
                border=ft.border.all(1, ft.Colors.GREY_800),
                on_click=_open_debug_console,
                tooltip="Статус Telegram-бота. Нажмите, чтобы открыть консоль отладки.",
            )

            def update_bot_status():
                try:
                    from bot import is_bot_active
                    active = is_bot_active()
                except Exception:
                    active = False

                def _ui_update():
                    if active:
                        bot_status_dot.color = ft.Colors.GREEN_ACCENT
                        bot_status_text.value = "Бот: Активен"
                        bot_status_text.color = ft.Colors.GREEN_100
                        bot_status_badge.border = ft.border.all(1, ft.Colors.GREEN_800)
                    else:
                        bot_status_dot.color = ft.Colors.RED_ACCENT
                        bot_status_text.value = "Бот: Неактивен"
                        bot_status_text.color = ft.Colors.RED_100
                        bot_status_badge.border = ft.border.all(1, ft.Colors.RED_800)
                    try:
                        bot_status_badge.update()
                    except Exception:
                        pass

                try:
                    if page.loop and page.loop.is_running():
                        page.loop.call_soon_threadsafe(_ui_update)
                    else:
                        _ui_update()
                except Exception:
                    pass

            def bot_status_poll_loop():
                import time
                while True:
                    update_bot_status()
                    time.sleep(5)

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
                update_bot_status()
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
                            bot_status_badge,
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
                        spacing=8,
                    ),
                ],
            )
            header_container = ft.Container(content=header, margin=ft.margin.only(bottom=10))

            # Daily Workload indicators setup
            load_container, _update_load_indicator = create_workload_indicator(db)

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

            page.add(ft.Column([header_container, load_container, tabs], expand=True, spacing=20))
            page.floating_action_button = fab

            # Initial trigger to populate the UI
            trigger_data_update()

            # Database Observer (watchdog)
            refresh_state = {"timer": None}

            def _safe_refresh():
                try:
                    # Считываем данные в фоновом потоке
                    app_state.reload()

                    # Обновляем UI в основном потоке событий Flet
                    def _ui_update():
                        _update_load_indicator()
                        update_bot_status()
                        send_desktop_notifications(
                            db,
                            notified_task_ids,
                            active_notification_tasks,
                            _on_notification_done,
                            last_notification_date_ref,
                        )
                        refresh_active_tab()

                    if page.loop and page.loop.is_running():
                        page.loop.call_soon_threadsafe(_ui_update)
                    else:
                        _ui_update()
                except Exception as ex:
                    logger.error(f"Error in _safe_refresh: {ex}")

            def _schedule_refresh():
                if refresh_state["timer"] is not None:
                    refresh_state["timer"].cancel()
                t = threading.Timer(0.3, _safe_refresh)
                refresh_state["timer"] = t
                t.start()

            observer = Observer()
            handler = DBChangeHandler(_schedule_refresh)
            observer.schedule(handler, path=str(db.db_path.parent), recursive=False)
            observer.start()

            def cleanup(e):
                if refresh_state["timer"] is not None:
                    refresh_state["timer"].cancel()
                observer.stop()
                observer.join()
                db.rotate_local_backups()
                try:
                    from bot import stop_bot_in_thread
                    stop_bot_in_thread()
                except Exception as ex:
                    logger.error(f"Error stopping bot on GUI exit: {ex}")

            threading.Thread(target=bot_status_poll_loop, daemon=True).start()
            page.on_disconnect = cleanup
            page.update()

        # При старте всегда открываем главный интерфейс
        show_dashboard()


    ft.app(target=main)
