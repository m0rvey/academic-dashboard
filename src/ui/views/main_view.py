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
from src.ui.constants import (
    BG_CARD,
    BG_CARD_BORDER,
    BG_DARK,
    BG_SIDEBAR,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_WARNING,
    FILTER_ALL,
    FILTER_ALL_TAGS,
    SORT_PRIORITY,
)
from src.ui.dialogs.add_edit_dialog import create_add_edit_dialog
from src.ui.dialogs.delete_dialog import create_delete_dialog
from src.ui.dialogs.shortcuts_dialog import create_shortcuts_dialog
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
    """Запускает графический интерфейс приложения в стиле macOS Cupertino."""
    from src.core.config import validate_env

    if not validate_env(exit_on_error=True):
        return

    db.rotate_local_backups()

    import sys
    if "pytest" not in sys.modules:
        from bot import start_bot_in_thread
        start_bot_in_thread()

    def main(page: ft.Page) -> None:
        from dotenv import load_dotenv

        from src.core.config import ENV_PATH

        load_dotenv(dotenv_path=ENV_PATH, override=True)

        try:
            page.window.min_width = 960
            page.window.min_height = 640
            page.window.width = 1120
            page.window.height = 760
        except Exception:
            pass

        def _open_debug_console(e=None):
            show_debug_console(page)

        def show_dashboard():
            page.clean()
            page.title = "Academic Dashboard"
            page.padding = 0
            page.spacing = 0
            page.bgcolor = BG_DARK

            # Bot status UI badge
            bot_status_dot = ft.Container(
                width=8,
                height=8,
                border_radius=4,
                bgcolor=COLOR_DANGER,
            )
            bot_status_text = ft.Text("Бот отключен", size=11, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_300)

            bot_status_badge = ft.Container(
                content=ft.Row(
                    [
                        bot_status_dot,
                        bot_status_text,
                    ],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                    tight=True,
                ),
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                border_radius=8,
                bgcolor=ft.Colors.with_opacity(0.15, BG_CARD),
                border=ft.border.all(1, BG_CARD_BORDER),
                on_click=_open_debug_console,
                tooltip="Статус Telegram-бота. Нажмите для открытия консоли отладки.",
            )

            def update_bot_status():
                try:
                    from bot import is_bot_active
                    active = is_bot_active()
                except Exception:
                    active = False

                def _ui_update():
                    if active:
                        bot_status_dot.bgcolor = COLOR_SUCCESS
                        bot_status_text.value = "Бот активен"
                        bot_status_text.color = COLOR_SUCCESS
                        bot_status_badge.border = ft.border.all(1, ft.Colors.with_opacity(0.4, COLOR_SUCCESS))
                    else:
                        bot_status_dot.bgcolor = COLOR_DANGER
                        bot_status_text.value = "Бот отключен"
                        bot_status_text.color = COLOR_DANGER
                        bot_status_badge.border = ft.border.all(1, ft.Colors.with_opacity(0.4, COLOR_DANGER))
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
                "active_nav": 0,
            }
            if config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        session_config.update(json.load(f))
                except Exception as ex:
                    logger.warning(f"Error loading session config: {ex}")

            page.theme_mode = ft.ThemeMode.DARK if session_config.get("theme_mode") == "dark" else ft.ThemeMode.LIGHT

            # Initialize global app state cache
            app_state = AppState(db)
            app_state.reload()

            # State tracking variables
            notified_task_ids = set()
            last_notification_date_ref = [date.today()]
            active_nav_index = [int(session_config.get("active_nav", 0))]

            config_write_lock = threading.Lock()

            def save_session_config():
                with config_write_lock:
                    session_config["theme_mode"] = "dark" if page.theme_mode == ft.ThemeMode.DARK else "light"
                    session_config["filter_status"] = filter_status.value
                    session_config["filter_tag"] = filter_tag.value
                    session_config["sort_by"] = sort_dropdown.value
                    session_config["active_nav"] = active_nav_index[0]
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
                theme_icon.icon = ft.Icons.DARK_MODE_ROUNDED if page.theme_mode == ft.ThemeMode.DARK else ft.Icons.LIGHT_MODE_ROUNDED
                theme_icon.icon_color = ft.Colors.BLUE_GREY if page.theme_mode == ft.ThemeMode.DARK else COLOR_WARNING
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
                _update_sidebar_badges()
                send_desktop_notifications(
                    db,
                    notified_task_ids,
                    last_notification_date_ref,
                )
                refresh_active_tab()

            # Initialize Modal Dialogs
            _, open_add_dialog, open_edit_dialog = create_add_edit_dialog(
                page, db, show_snack, lambda: trigger_data_update()
            )
            _, open_delete_confirm = create_delete_dialog(
                page, db, show_snack, lambda: trigger_data_update()
            )
            shortcuts_dialog = create_shortcuts_dialog(page)

            # Initialize Views
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

            view_contents = [tasks_view, stats_view, grades_view, calendar_view]
            main_content_container = ft.Container(
                content=view_contents[active_nav_index[0]],
                expand=True,
                padding=ft.padding.symmetric(horizontal=20, vertical=14),
            )

            # Task count badge in sidebar
            tasks_badge_text = ft.Text("0", size=10, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY)
            tasks_badge = ft.Container(
                content=tasks_badge_text,
                bgcolor=ft.Colors.with_opacity(0.18, COLOR_PRIMARY),
                padding=ft.padding.symmetric(horizontal=7, vertical=2),
                border_radius=10,
                visible=False,
            )

            def _update_sidebar_badges():
                try:
                    active_tasks = app_state.get_active_tasks()
                    cnt = len(active_tasks)
                    if cnt > 0:
                        tasks_badge_text.value = str(cnt)
                        tasks_badge.visible = True
                    else:
                        tasks_badge.visible = False
                    tasks_badge.update()
                except Exception:
                    pass

            # Sidebar Navigation Items
            nav_items_data = [
                ("Задачи", ft.Icons.FORMAT_LIST_BULLETED_ROUNDED, tasks_badge),
                ("Статистика", ft.Icons.INSIGHTS_ROUNDED, None),
                ("Успеваемость", ft.Icons.SCHOOL_ROUNDED, None),
                ("Календарь", ft.Icons.CALENDAR_MONTH_ROUNDED, None),
            ]

            nav_buttons = []

            def switch_nav(idx: int):
                active_nav_index[0] = idx
                main_content_container.content = view_contents[idx]
                save_session_config()
                _update_sidebar_styles()
                refresh_active_tab()
                page.update()

            def _update_sidebar_styles():
                for idx, (btn, _, _) in enumerate(nav_buttons):
                    is_active = idx == active_nav_index[0]
                    btn.bgcolor = ft.Colors.with_opacity(0.15, COLOR_PRIMARY) if is_active else ft.Colors.TRANSPARENT
                    btn.border = ft.border.all(1, ft.Colors.with_opacity(0.3, COLOR_PRIMARY)) if is_active else None
                    btn.content.controls[0].controls[0].color = COLOR_PRIMARY if is_active else ft.Colors.GREY_400
                    btn.content.controls[0].controls[1].color = ft.Colors.WHITE if is_active else ft.Colors.GREY_300
                    btn.content.controls[0].controls[1].weight = ft.FontWeight.BOLD if is_active else ft.FontWeight.W_500

            for idx, (title, icon, badge_elem) in enumerate(nav_items_data):
                row_items = [
                    ft.Icon(icon, size=18, color=ft.Colors.GREY_400),
                    ft.Text(title, size=13, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_300),
                ]
                btn_content = ft.Row(
                    [
                        ft.Row(row_items, spacing=10),
                        *( [badge_elem] if badge_elem else [] ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
                btn = ft.Container(
                    content=btn_content,
                    padding=ft.padding.symmetric(horizontal=12, vertical=9),
                    border_radius=8,
                    on_click=lambda e, i=idx: switch_nav(i),
                    animate=100,
                )
                nav_buttons.append((btn, title, icon))

            _update_sidebar_styles()

            # Sidebar layout
            sidebar = ft.Container(
                width=220,
                bgcolor=BG_SIDEBAR,
                border=ft.border.only(right=ft.BorderSide(1, BG_CARD_BORDER)),
                padding=ft.padding.symmetric(horizontal=12, vertical=16),
                content=ft.Column(
                    [
                        # Brand Header
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Icon(ft.Icons.SCHOOL_ROUNDED, size=20, color=COLOR_PRIMARY),
                                    bgcolor=ft.Colors.with_opacity(0.15, COLOR_PRIMARY),
                                    padding=6,
                                    border_radius=8,
                                ),
                                ft.Column(
                                    [
                                        ft.Text("Academic", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                        ft.Text("Dashboard macOS", size=10, color=ft.Colors.GREY_400),
                                    ],
                                    spacing=0,
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.Container(height=10),
                        # Quick Add Button
                        ft.FilledButton(
                            "Новая задача",
                            icon=ft.Icons.ADD_ROUNDED,
                            width=196,
                            on_click=open_add_dialog,
                        ),
                        ft.Container(height=10),
                        ft.Text("НАВИГАЦИЯ", size=10, color=ft.Colors.GREY_500, weight=ft.FontWeight.BOLD),
                        ft.Column([b[0] for b in nav_buttons], spacing=4),
                        ft.Container(expand=True),
                        # Sidebar Footer with Bot status and hotkeys helper
                        ft.Divider(color=BG_CARD_BORDER, height=1),
                        ft.Row(
                            [
                                bot_status_badge,
                                ft.IconButton(
                                    icon=ft.Icons.KEYBOARD_ROUNDED,
                                    icon_size=16,
                                    icon_color=COLOR_PRIMARY,
                                    tooltip="Горячие клавиши (Cmd+/)",
                                    on_click=lambda e: page.open(shortcuts_dialog),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    ],
                    spacing=6,
                    expand=True,
                ),
            )

            # Daily Workload indicator
            load_container, _update_load_indicator = create_workload_indicator(db)

            # Top action bar
            theme_icon = ft.IconButton(
                icon=(ft.Icons.LIGHT_MODE_ROUNDED if page.theme_mode == ft.ThemeMode.DARK else ft.Icons.DARK_MODE_ROUNDED),
                icon_color=(COLOR_WARNING if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.BLUE_GREY),
                on_click=toggle_theme,
                tooltip="Сменить тему оформления (Cmd+T)",
            )

            topbar = ft.Container(
                content=ft.Row(
                    [
                        ft.Container(content=load_container, expand=True),
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.FILE_DOWNLOAD_OUTLINED,
                                    icon_color=COLOR_PRIMARY,
                                    on_click=import_data,
                                    tooltip="Импорт из JSON",
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.FILE_UPLOAD_OUTLINED,
                                    icon_color=COLOR_PRIMARY,
                                    on_click=export_data,
                                    tooltip="Экспорт в JSON",
                                ),
                                theme_icon,
                            ],
                            spacing=4,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.only(left=20, right=20, top=14, bottom=6),
            )

            # Main content column
            right_content = ft.Column(
                [
                    topbar,
                    main_content_container,
                ],
                expand=True,
                spacing=0,
            )

            def refresh_active_tab(e=None):
                idx = active_nav_index[0]
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
                                tasks_view=tasks_view,
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

            def handle_keyboard_shortcuts(e: ft.KeyboardEvent):
                is_cmd_or_ctrl = e.ctrl or e.meta
                if not is_cmd_or_ctrl:
                    return

                key_upper = (e.key or "").upper()
                if key_upper == "N":
                    open_add_dialog(None)
                elif key_upper == "F":
                    if active_nav_index[0] != 0:
                        switch_nav(0)
                    search_field.focus()
                elif key_upper == "R":
                    trigger_data_update()
                    show_snack("🔄 Данные успешно обновлены")
                elif key_upper == "T":
                    toggle_theme(None)
                    show_snack(
                        f"🎨 Тема переключена на {'тёмную' if page.theme_mode == ft.ThemeMode.DARK else 'светлую'}"
                    )
                elif key_upper in ("1", "2", "3", "4"):
                    dest_idx = int(key_upper) - 1
                    switch_nav(dest_idx)
                elif key_upper in ("/", "?"):
                    page.open(shortcuts_dialog)

            page.on_keyboard_event = handle_keyboard_shortcuts

            page.floating_action_button = ft.FloatingActionButton(
                icon=ft.Icons.ADD_ROUNDED,
                bgcolor=COLOR_PRIMARY,
                on_click=open_add_dialog,
                tooltip="Новая задача (Cmd+N)",
            )

            # Master macOS Layout (Sidebar on the left, Views on the right)
            page.add(
                ft.Row(
                    [
                        sidebar,
                        right_content,
                    ],
                    expand=True,
                    spacing=0,
                )
            )

            # Initial trigger to populate the UI
            trigger_data_update()

            # Database Observer (watchdog)
            refresh_state = {"timer": None}

            def _safe_refresh():
                try:
                    app_state.reload()

                    def _ui_update():
                        _update_load_indicator()
                        update_bot_status()
                        _update_sidebar_badges()
                        send_desktop_notifications(
                            db,
                            notified_task_ids,
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

        show_dashboard()

    ft.app(target=main)
