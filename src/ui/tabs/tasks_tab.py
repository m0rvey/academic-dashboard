from datetime import date

import flet as ft

from src.core.database import DatabaseManager
from src.core.logger import setup_logger
from src.core.models import TaskStatus
from src.ui.components.task_card import TaskCard
from src.ui.constants import (
    BG_CARD,
    BG_CARD_BORDER,
    CHIP_ALL,
    CHIP_DONE,
    CHIP_EXAMS,
    CHIP_OVERDUE,
    CHIP_TODAY,
    CHIP_URGENT,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_WARNING,
    FILTER_ALL,
    FILTER_ALL_TAGS,
    SORT_DEADLINE,
    SORT_EFFORT,
    SORT_PRIORITY,
    SORT_SUBJECT,
    STATUS_DOING,
    STATUS_DONE,
    STATUS_TODO,
)

logger = setup_logger("tasks_tab")


def create_tasks_tab(session_config, save_session_config, refresh_all):
    """Создаёт и возвращает содержимое вкладки «Задачи» со списком/канбаном и фильтр-чипами."""

    active_chip = [session_config.get("active_chip", CHIP_ALL)]
    view_mode = [session_config.get("view_mode", "list")]  # 'list' или 'kanban'

    def _on_filter_change(e):
        task_list.display_count = 50
        save_session_config()
        refresh_all()

    def _reset_and_refresh(e):
        task_list.display_count = 50
        refresh_all()

    search_field = ft.TextField(
        hint_text="Поиск задач по предмету, описанию или тегу...",
        expand=True,
        prefix_icon=ft.Icons.SEARCH_ROUNDED,
        on_change=_reset_and_refresh,
        border_radius=10,
        border_color=BG_CARD_BORDER,
        focused_border_color=COLOR_PRIMARY,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=10),
        dense=True,
    )

    filter_status = ft.Dropdown(
        label="Статус",
        options=[
            ft.dropdown.Option(FILTER_ALL),
            ft.dropdown.Option(STATUS_TODO),
            ft.dropdown.Option(STATUS_DOING),
            ft.dropdown.Option(STATUS_DONE),
        ],
        value=session_config["filter_status"],
        width=130,
        on_change=_on_filter_change,
        border_radius=10,
        border_color=BG_CARD_BORDER,
        focused_border_color=COLOR_PRIMARY,
        dense=True,
    )

    filter_tag = ft.Dropdown(
        label="Тег",
        options=[ft.dropdown.Option(FILTER_ALL_TAGS)],
        value=session_config["filter_tag"],
        width=130,
        on_change=_on_filter_change,
        border_radius=10,
        border_color=BG_CARD_BORDER,
        focused_border_color=COLOR_PRIMARY,
        dense=True,
    )

    sort_dropdown = ft.Dropdown(
        label="Сортировка",
        options=[
            ft.dropdown.Option(SORT_PRIORITY),
            ft.dropdown.Option(SORT_DEADLINE),
            ft.dropdown.Option(SORT_EFFORT),
            ft.dropdown.Option(SORT_SUBJECT),
        ],
        value=session_config["sort_by"],
        width=175,
        on_change=_on_filter_change,
        border_radius=10,
        border_color=BG_CARD_BORDER,
        focused_border_color=COLOR_PRIMARY,
        dense=True,
    )

    # Быстрые фильтр-чипы
    chips_list = [CHIP_ALL, CHIP_URGENT, CHIP_TODAY, CHIP_OVERDUE, CHIP_EXAMS, CHIP_DONE]
    chips_controls = []

    def set_chip(chip_name):
        active_chip[0] = chip_name
        session_config["active_chip"] = chip_name
        _update_chips_ui()
        refresh_all()

    def _update_chips_ui():
        for chip_btn, c_name in chips_controls:
            is_sel = c_name == active_chip[0]
            chip_btn.bgcolor = (
                ft.Colors.with_opacity(0.18, COLOR_PRIMARY) if is_sel else ft.Colors.with_opacity(0.05, ft.Colors.WHITE)
            )
            chip_btn.border = ft.border.all(
                1, COLOR_PRIMARY if is_sel else BG_CARD_BORDER
            )
            chip_btn.content.color = COLOR_PRIMARY if is_sel else ft.Colors.GREY_300

    chips_row = ft.Row(spacing=8, scroll=ft.ScrollMode.AUTO)
    for c_name in chips_list:
        chip_btn = ft.Container(
            content=ft.Text(c_name, size=12, weight=ft.FontWeight.W_600),
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            border_radius=20,
            on_click=lambda e, name=c_name: set_chip(name),
            animate=150,
        )
        chips_controls.append((chip_btn, c_name))
        chips_row.controls.append(chip_btn)

    _update_chips_ui()

    # Переключатель видов Список / Канбан
    def toggle_view_mode(mode):
        view_mode[0] = mode
        session_config["view_mode"] = mode
        btn_list.bgcolor = ft.Colors.with_opacity(0.2, COLOR_PRIMARY) if mode == "list" else ft.Colors.TRANSPARENT
        btn_kanban.bgcolor = ft.Colors.with_opacity(0.2, COLOR_PRIMARY) if mode == "kanban" else ft.Colors.TRANSPARENT
        refresh_all()

    btn_list = ft.IconButton(
        icon=ft.Icons.VIEW_LIST_ROUNDED,
        icon_color=COLOR_PRIMARY,
        tooltip="Режим списка",
        bgcolor=ft.Colors.with_opacity(0.2, COLOR_PRIMARY) if view_mode[0] == "list" else ft.Colors.TRANSPARENT,
        on_click=lambda e: toggle_view_mode("list"),
    )
    btn_kanban = ft.IconButton(
        icon=ft.Icons.VIEW_KANBAN_ROUNDED,
        icon_color=COLOR_PRIMARY,
        tooltip="Канбан-доска",
        bgcolor=ft.Colors.with_opacity(0.2, COLOR_PRIMARY) if view_mode[0] == "kanban" else ft.Colors.TRANSPARENT,
        on_click=lambda e: toggle_view_mode("kanban"),
    )

    view_switcher = ft.Container(
        content=ft.Row([btn_list, btn_kanban], spacing=2),
        border=ft.border.all(1, BG_CARD_BORDER),
        border_radius=10,
        padding=ft.padding.all(2),
    )

    refresh_btn = ft.IconButton(
        icon=ft.Icons.REFRESH_ROUNDED,
        icon_color=COLOR_PRIMARY,
        tooltip="Обновить данные (Cmd+R)",
        on_click=lambda e: refresh_all(),
    )

    top_controls_row = ft.Row(
        [
            search_field,
            filter_status,
            filter_tag,
            sort_dropdown,
            view_switcher,
            refresh_btn,
        ],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    task_list = ft.ListView(expand=True, spacing=8, padding=ft.padding.only(right=4))
    task_list.display_count = 50

    kanban_container = ft.Row(
        expand=True,
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.START,
        scroll=ft.ScrollMode.AUTO,
    )

    content_area = ft.Container(
        content=task_list,
        expand=True,
    )

    tasks_view = ft.Column(
        [
            top_controls_row,
            chips_row,
            content_area,
        ],
        expand=True,
        spacing=10,
    )

    tasks_view.active_chip = active_chip
    tasks_view.view_mode = view_mode
    tasks_view.content_area = content_area
    tasks_view.kanban_container = kanban_container

    return tasks_view, search_field, filter_status, filter_tag, sort_dropdown, task_list


def update_task_list(
    db: DatabaseManager,
    search_field: ft.TextField,
    filter_status: ft.Dropdown,
    filter_tag: ft.Dropdown,
    sort_dropdown: ft.Dropdown,
    task_list: ft.ListView,
    refresh_all,
    open_edit_dialog,
    open_delete_confirm,
    tasks_view: ft.Column = None,
) -> None:
    """Обновляет список задач в соответствии с активными чип-фильтрами и выбранным режимом (Список / Канбан)."""
    try:
        all_tags = db.get_all_tags()
    except Exception as e:
        logger.warning(f"Error fetching tags: {e}")
        all_tags = []

    current_tag = filter_tag.value
    filter_tag.options = [ft.dropdown.Option(FILTER_ALL_TAGS)] + [ft.dropdown.Option(tag) for tag in all_tags]

    if current_tag in all_tags or current_tag == FILTER_ALL_TAGS:
        filter_tag.value = current_tag
    else:
        filter_tag.value = FILTER_ALL_TAGS

    status_map = {
        STATUS_TODO: TaskStatus.TODO,
        STATUS_DOING: TaskStatus.DOING,
        STATUS_DONE: TaskStatus.DONE,
    }
    db_status = status_map.get(filter_status.value)
    db_tag = None if filter_tag.value == FILTER_ALL_TAGS else filter_tag.value

    sort_map = {
        SORT_DEADLINE: "deadline",
        SORT_EFFORT: "effort",
        SORT_SUBJECT: "subject",
        SORT_PRIORITY: "priority",
    }
    db_sort = sort_map.get(sort_dropdown.value, "priority")

    try:
        sorted_tasks = db.get_filtered_tasks(
            search_query=search_field.value,
            status=db_status,
            tag=db_tag,
            sort_by=db_sort,
        )
    except Exception as e:
        logger.warning(f"Error filtering tasks: {e}")
        sorted_tasks = []

    # Применение быстрого чип-фильтра
    active_chip = tasks_view.active_chip[0] if tasks_view and hasattr(tasks_view, "active_chip") else CHIP_ALL
    today_date = date.today()

    if active_chip == CHIP_URGENT:
        sorted_tasks = [t for t in sorted_tasks if t.status != TaskStatus.DONE and (t.deadline_date <= today_date or t.effort_score >= 7)]
    elif active_chip == CHIP_TODAY:
        sorted_tasks = [t for t in sorted_tasks if t.deadline_date == today_date]
    elif active_chip == CHIP_OVERDUE:
        sorted_tasks = [t for t in sorted_tasks if t.status != TaskStatus.DONE and t.deadline_date < today_date]
    elif active_chip == CHIP_EXAMS:
        sorted_tasks = [t for t in sorted_tasks if any(tag in ("ОГЭ", "ЕГЭ", "Экзамен") for tag in t.tags)]
    elif active_chip == CHIP_DONE:
        sorted_tasks = [t for t in sorted_tasks if t.status == TaskStatus.DONE]

    mode = tasks_view.view_mode[0] if tasks_view and hasattr(tasks_view, "view_mode") else "list"

    if mode == "kanban":
        _render_kanban_view(sorted_tasks, db, refresh_all, open_edit_dialog, open_delete_confirm, tasks_view)
    else:
        _render_list_view(sorted_tasks, db, refresh_all, open_edit_dialog, open_delete_confirm, task_list, tasks_view)


def _render_list_view(sorted_tasks, db, refresh_all, open_edit_dialog, open_delete_confirm, task_list, tasks_view):
    """Отрисовывает задачи в виде структурированного списка с группировкой по срочности."""
    if tasks_view and hasattr(tasks_view, "content_area"):
        tasks_view.content_area.content = task_list

    today_date = date.today()
    overdue = []
    today_tasks_list = []
    upcoming = []
    done_tasks = []

    for task in sorted_tasks:
        t_deadline = task.deadline_date
        if task.status == TaskStatus.DONE:
            done_tasks.append(task)
        elif t_deadline < today_date:
            overdue.append(task)
        elif t_deadline == today_date:
            today_tasks_list.append(task)
        else:
            upcoming.append(task)

    new_controls = []
    rendered_count = 0
    display_limit = getattr(task_list, "display_count", 50)

    def add_section(title, task_group, color, icon):
        nonlocal rendered_count
        if not task_group or rendered_count >= display_limit:
            return

        group_to_render = []
        for t in task_group:
            if rendered_count >= display_limit:
                break
            group_to_render.append(t)
            rendered_count += 1

        if group_to_render:
            new_controls.append(
                ft.Container(
                    key=f"header_{title}",
                    content=ft.Row(
                        [
                            ft.Icon(icon, size=16, color=color),
                            ft.Text(f"{title} ({len(task_group)})", size=14, weight=ft.FontWeight.BOLD, color=color),
                        ],
                        spacing=6,
                    ),
                    padding=ft.padding.only(top=10, bottom=4, left=4),
                )
            )
            for t in group_to_render:
                new_controls.append(TaskCard(t, db, refresh_all, open_edit_dialog, open_delete_confirm))

    add_section("Просроченные задачи", overdue, COLOR_DANGER, ft.Icons.WARNING_AMBER_ROUNDED)
    add_section("Задачи на сегодня", today_tasks_list, COLOR_WARNING, ft.Icons.TIMER_OUTLINED)
    add_section("Предстоящие задачи", upcoming, COLOR_PRIMARY, ft.Icons.UPCOMING_ROUNDED)
    add_section("Выполненные задачи", done_tasks, COLOR_SUCCESS, ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED)

    if not sorted_tasks:
        new_controls.append(
            ft.Container(
                key="empty_state",
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.TASK_ALT_ROUNDED, size=52, color=ft.Colors.GREY_600),
                        ft.Text(
                            "Нет задач по выбранным критериям",
                            size=15,
                            color=ft.Colors.GREY_400,
                            weight=ft.FontWeight.W_600,
                        ),
                        ft.Text(
                            "Попробуйте изменить фильтры или добавьте новую задачу (Cmd+N)",
                            size=12,
                            color=ft.Colors.GREY_500,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                ),
                padding=60,
                alignment=ft.alignment.center,
            )
        )

    task_list.controls = new_controls


def _render_kanban_view(sorted_tasks, db, refresh_all, open_edit_dialog, open_delete_confirm, tasks_view):
    """Отрисовывает задачи в виде 3 колонок Канбан-доски (TODO, DOING, DONE)."""
    if not tasks_view or not hasattr(tasks_view, "kanban_container"):
        return

    kanban_container = tasks_view.kanban_container
    tasks_view.content_area.content = kanban_container

    todo_tasks = [t for t in sorted_tasks if t.status == TaskStatus.TODO]
    doing_tasks = [t for t in sorted_tasks if t.status == TaskStatus.DOING]
    done_tasks = [t for t in sorted_tasks if t.status == TaskStatus.DONE]

    def build_column(title, count, tasks, color, icon):
        card_items = []
        for t in tasks:
            card_items.append(TaskCard(t, db, refresh_all, open_edit_dialog, open_delete_confirm))

        col_content = ft.Column(
            card_items,
            scroll=ft.ScrollMode.AUTO,
            spacing=8,
            expand=True,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(icon, size=16, color=color),
                                        ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                    ],
                                    spacing=6,
                                ),
                                ft.Container(
                                    content=ft.Text(str(count), size=11, color=color, weight=ft.FontWeight.BOLD),
                                    bgcolor=ft.Colors.with_opacity(0.15, color),
                                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                    border_radius=10,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        border_radius=10,
                        bgcolor=BG_CARD,
                        border=ft.border.all(1, BG_CARD_BORDER),
                    ),
                    col_content,
                ],
                spacing=8,
                expand=True,
            ),
            bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
            border_radius=12,
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            padding=8,
            expand=True,
        )

    kanban_container.controls = [
        build_column("К выполнению", len(todo_tasks), todo_tasks, COLOR_PRIMARY, ft.Icons.FORMAT_LIST_BULLETED_ROUNDED),
        build_column("В процессе", len(doing_tasks), doing_tasks, COLOR_WARNING, ft.Icons.BOLT_ROUNDED),
        build_column("Выполнено", len(done_tasks), done_tasks, COLOR_SUCCESS, ft.Icons.CHECK_CIRCLE_ROUNDED),
    ]
