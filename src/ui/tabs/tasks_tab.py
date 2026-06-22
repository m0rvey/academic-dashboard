from datetime import date

import flet as ft

from src.core.database import DatabaseManager
from src.core.logger import setup_logger
from src.core.models import TaskStatus
from src.ui.components.task_card import TaskCard
from src.ui.constants import (
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
    """Создаёт и возвращает содержимое вкладки «Задачи» и её основные элементы управления."""

    def _on_filter_change(e):
        task_list.display_count = 30
        save_session_config()
        refresh_all()

    def _reset_and_refresh(e):
        task_list.display_count = 30
        refresh_all()

    search_field = ft.TextField(
        label="Поиск задач",
        expand=True,
        prefix_icon=ft.Icons.SEARCH,
        on_change=_reset_and_refresh,
        border_radius=8,
        border_color=ft.Colors.GREY_800,
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
        border_radius=8,
        border_color=ft.Colors.GREY_800,
    )
    filter_tag = ft.Dropdown(
        label="Тег",
        options=[ft.dropdown.Option(FILTER_ALL_TAGS)],
        value=session_config["filter_tag"],
        width=130,
        on_change=_on_filter_change,
        border_radius=8,
        border_color=ft.Colors.GREY_800,
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
        width=180,
        on_change=_on_filter_change,
        border_radius=8,
        border_color=ft.Colors.GREY_800,
    )

    refresh_btn = ft.IconButton(
        icon=ft.Icons.REFRESH_ROUNDED,
        icon_color=ft.Colors.LIGHT_BLUE_200,
        tooltip="Обновить данные",
        on_click=lambda e: refresh_all(),
    )

    filters_row = ft.Row([search_field, filter_status, filter_tag, sort_dropdown, refresh_btn], spacing=10)
    task_list = ft.ListView(expand=True, spacing=10, padding=5)
    task_list.display_count = 30

    tasks_view = ft.Column([filters_row, task_list], expand=True, spacing=10)

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
) -> None:
    """Обновляет список задач: получает отфильтрованные данные из БД и перестраивает UI-контролы."""
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

    new_controls = []

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

    if not hasattr(task_list, "display_count"):
        task_list.display_count = 30

    rendered_count = 0

    def add_section(title, task_group, color):
        nonlocal rendered_count
        if not task_group or rendered_count >= task_list.display_count:
            return

        group_to_render = []
        for t in task_group:
            if rendered_count >= task_list.display_count:
                break
            group_to_render.append(t)
            rendered_count += 1

        if group_to_render:
            new_controls.append(
                ft.Container(
                    key=f"header_{title}",
                    content=ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=color),
                    padding=ft.padding.only(top=10, bottom=5),
                )
            )
            for t in group_to_render:
                new_controls.append(TaskCard(t, db, refresh_all, open_edit_dialog, open_delete_confirm))

    add_section("🔴 Просроченные", overdue, ft.Colors.RED_400)
    add_section("🟢 На сегодня", today_tasks_list, ft.Colors.GREEN_400)
    add_section("🔵 Предстоящие", upcoming, ft.Colors.BLUE_400)
    add_section("⚪ Выполненные", done_tasks, ft.Colors.GREY_500)

    if not sorted_tasks:
        new_controls.append(
            ft.Container(
                key="empty_state",
                content=ft.Column(
                    [
                        ft.Icon(
                            ft.Icons.ASSIGNMENT_OUTLINED,
                            size=48,
                            color=ft.Colors.GREY_600,
                        ),
                        ft.Text(
                            "Список задач пуст или ничего не найдено",
                            size=14,
                            color=ft.Colors.GREY_500,
                            weight=ft.FontWeight.W_500,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=50,
                alignment=ft.alignment.center,
            )
        )
    elif len(sorted_tasks) > task_list.display_count:

        def load_more(e):
            task_list.display_count += 30
            refresh_all()

        new_controls.append(
            ft.Container(
                content=ft.OutlinedButton(
                    "Показать ещё",
                    icon=ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED,
                    on_click=load_more,
                    width=200,
                ),
                alignment=ft.alignment.center,
                padding=ft.padding.only(top=10, bottom=20),
            )
        )

    task_list.controls = new_controls
