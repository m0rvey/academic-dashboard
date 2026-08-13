from datetime import date

import flet as ft

from src.core.database import DatabaseManager
from src.core.logger import setup_logger
from src.core.logic import calculate_priority
from src.core.models import Task, TaskStatus
from src.ui.components.task_card import TaskCard
from src.ui.constants import (
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
    get_theme_palette,
)

logger = setup_logger("tasks_tab")


class KanbanCard(ft.Container):
    """Специализированная карточка задачи для колонок Канбан-доски с быстрыми действиями."""

    def __init__(
        self,
        task: Task,
        db: DatabaseManager,
        refresh_all,
        open_edit_dialog,
        open_delete_confirm,
        is_dark: bool = True,
    ):
        super().__init__()
        self.task = task
        self.db = db
        self.refresh_all = refresh_all
        self.open_edit_dialog = open_edit_dialog
        self.open_delete_confirm = open_delete_confirm
        self.is_dark = is_dark
        self.palette = get_theme_palette(is_dark)

        self.padding = ft.padding.all(12)
        self.border_radius = 10
        self.bgcolor = self.palette["bg_card"]
        self.scale = 1.0
        self.animate_scale = 150

        self.priority = calculate_priority(self.task)
        self.build_ui()

    def _get_indicator_color(self) -> str:
        if self.task.status == TaskStatus.DONE:
            return COLOR_SUCCESS
        elif self.task.status == TaskStatus.DOING:
            return COLOR_WARNING
        elif self.priority >= 2.5:
            return COLOR_DANGER
        elif self.priority >= 1.5:
            return COLOR_WARNING
        return COLOR_PRIMARY

    def _get_deadline_chip(self) -> ft.Container:
        try:
            deadline_date = date.fromisoformat(self.task.deadline)
            today = date.today()
            delta_days = (deadline_date - today).days

            if self.task.status == TaskStatus.DONE:
                text = self.task.deadline
                bg = ft.Colors.with_opacity(0.12, COLOR_SUCCESS)
                color = COLOR_SUCCESS
                icon = ft.Icons.CHECK_CIRCLE_OUTLINE
            elif delta_days < 0:
                text = f"Просрочено ({abs(delta_days)} д.)"
                bg = ft.Colors.with_opacity(0.15, COLOR_DANGER)
                color = COLOR_DANGER
                icon = ft.Icons.WARNING_AMBER_ROUNDED
            elif delta_days == 0:
                text = "🔥 Сегодня!"
                bg = ft.Colors.with_opacity(0.18, COLOR_DANGER)
                color = COLOR_DANGER
                icon = ft.Icons.TIMER
            elif delta_days == 1:
                text = "⚡ Завтра"
                bg = ft.Colors.with_opacity(0.15, COLOR_WARNING)
                color = COLOR_WARNING
                icon = ft.Icons.ACCESS_TIME
            else:
                text = f"До {self.task.deadline}"
                bg = ft.Colors.with_opacity(0.08, ft.Colors.BLUE_GREY)
                color = self.palette["text_secondary"]
                icon = ft.Icons.CALENDAR_TODAY
        except Exception:
            text = self.task.deadline
            bg = ft.Colors.with_opacity(0.08, ft.Colors.BLUE_GREY)
            color = self.palette["text_secondary"]
            icon = ft.Icons.CALENDAR_TODAY

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, size=10, color=color),
                    ft.Text(text, size=10, color=color, weight=ft.FontWeight.W_600),
                ],
                spacing=3,
                tight=True,
            ),
            bgcolor=bg,
            padding=ft.padding.symmetric(horizontal=6, vertical=3),
            border_radius=6,
        )

    def _move_task(self, target_status: TaskStatus):
        self.db.update_task_status(self.task.id, target_status)
        self.refresh_all()

    def build_ui(self):
        indicator_color = self._get_indicator_color()

        self.border = ft.Border(
            left=ft.BorderSide(4, indicator_color),
            top=ft.BorderSide(1, self.palette["bg_card_border"]),
            right=ft.BorderSide(1, self.palette["bg_card_border"]),
            bottom=ft.BorderSide(1, self.palette["bg_card_border"]),
        )

        is_done = self.task.status == TaskStatus.DONE
        text_decor = ft.TextDecoration.LINE_THROUGH if is_done else None
        text_color = self.palette["text_muted"] if is_done else self.palette["text_primary"]
        desc_color = self.palette["text_muted"] if is_done else self.palette["text_secondary"]

        # Теги
        tags_ui = []
        for t in self.task.tags:
            is_exam = t in ("ОГЭ", "ЕГЭ", "Экзамен")
            tag_color = COLOR_DANGER if is_exam else self.palette["text_secondary"]
            tag_bg = ft.Colors.with_opacity(0.15, COLOR_DANGER) if is_exam else ft.Colors.with_opacity(0.1, ft.Colors.BLUE_GREY)
            tags_ui.append(
                ft.Container(
                    content=ft.Text(f"#{t}", size=9, color=tag_color, weight=ft.FontWeight.W_600),
                    bgcolor=tag_bg,
                    padding=ft.padding.symmetric(horizontal=5, vertical=2),
                    border_radius=4,
                )
            )

        # Кнопки быстрых переходов
        action_buttons = []
        if self.task.status == TaskStatus.TODO:
            action_buttons.append(
                ft.TextButton(
                    "⚡ В процесс",
                    icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                    style=ft.ButtonStyle(
                        color=COLOR_WARNING,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        text_style=ft.TextStyle(size=11, weight=ft.FontWeight.BOLD),
                    ),
                    on_click=lambda e: self._move_task(TaskStatus.DOING),
                )
            )
        elif self.task.status == TaskStatus.DOING:
            action_buttons.append(
                ft.TextButton(
                    "В план",
                    icon=ft.Icons.ARROW_BACK_ROUNDED,
                    style=ft.ButtonStyle(
                        color=COLOR_PRIMARY,
                        padding=ft.padding.symmetric(horizontal=6, vertical=4),
                        text_style=ft.TextStyle(size=10),
                    ),
                    on_click=lambda e: self._move_task(TaskStatus.TODO),
                )
            )
            action_buttons.append(
                ft.TextButton(
                    "Готово",
                    icon=ft.Icons.CHECK_ROUNDED,
                    style=ft.ButtonStyle(
                        color=COLOR_SUCCESS,
                        padding=ft.padding.symmetric(horizontal=6, vertical=4),
                        text_style=ft.TextStyle(size=11, weight=ft.FontWeight.BOLD),
                    ),
                    on_click=lambda e: self._move_task(TaskStatus.DONE),
                )
            )
        elif self.task.status == TaskStatus.DONE:
            action_buttons.append(
                ft.TextButton(
                    "Вернуть",
                    icon=ft.Icons.REPLAY_ROUNDED,
                    style=ft.ButtonStyle(
                        color=COLOR_WARNING,
                        padding=ft.padding.symmetric(horizontal=6, vertical=4),
                        text_style=ft.TextStyle(size=10),
                    ),
                    on_click=lambda e: self._move_task(TaskStatus.DOING),
                )
            )
            # Оценка в Kanban
            def _on_grade(e):
                val = int(e.control.value) if e.control.value != "None" else None
                self.db.update_task_grade(self.task.id, val)
                self.refresh_all()

            action_buttons.append(
                ft.Container(
                    content=ft.Dropdown(
                        value=(str(self.task.grade) if self.task.grade is not None else "None"),
                        options=[
                            ft.dropdown.Option("None", "—"),
                            ft.dropdown.Option("5", "5 (Отл)"),
                            ft.dropdown.Option("4", "4 (Хор)"),
                            ft.dropdown.Option("3", "3 (Уд)"),
                            ft.dropdown.Option("2", "2 (Неуд)"),
                        ],
                        width=82,
                        text_size=10,
                        content_padding=ft.padding.symmetric(horizontal=4, vertical=0),
                        border_radius=6,
                        border_color=ft.Colors.with_opacity(0.4, COLOR_SUCCESS),
                        on_change=_on_grade,
                    ),
                    height=28,
                    width=82,
                )
            )

        self.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(
                            self.task.subject,
                            weight=ft.FontWeight.BOLD,
                            size=13,
                            color=text_color,
                            style=ft.TextStyle(decoration=text_decor),
                            expand=True,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.EDIT_OUTLINED,
                            icon_color=COLOR_PRIMARY,
                            icon_size=14,
                            tooltip="Редактировать",
                            on_click=lambda e: self.open_edit_dialog(self.task),
                            style=ft.ButtonStyle(padding=ft.padding.all(0)),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                            icon_color=COLOR_DANGER,
                            icon_size=14,
                            tooltip="Удалить",
                            on_click=lambda e: self.open_delete_confirm(self.task.id, self.task.subject),
                            style=ft.ButtonStyle(padding=ft.padding.all(0)),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    spacing=2,
                ),
                *(
                    [
                        ft.Text(
                            self.task.description,
                            size=11,
                            color=desc_color,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        )
                    ]
                    if self.task.description
                    else []
                ),
                ft.Row(
                    [
                        self._get_deadline_chip(),
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.BOLT, size=10, color=COLOR_WARNING),
                                    ft.Text(f"{self.task.effort_score}", size=10, color=COLOR_WARNING, weight=ft.FontWeight.BOLD),
                                ],
                                spacing=2,
                                tight=True,
                            ),
                            bgcolor=ft.Colors.with_opacity(0.1, COLOR_WARNING),
                            padding=ft.padding.symmetric(horizontal=5, vertical=3),
                            border_radius=6,
                        ),
                        *tags_ui,
                    ],
                    wrap=True,
                    spacing=4,
                ),
                ft.Divider(color=self.palette["bg_card_border"], height=1),
                ft.Row(
                    action_buttons,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=6,
        )

        def on_hover(e):
            is_hovered = e.data == "true"
            self.scale = 1.015 if is_hovered else 1.0
            self.bgcolor = self.palette["bg_card_hover"] if is_hovered else self.palette["bg_card"]
            self.shadow = (
                ft.BoxShadow(
                    blur_radius=10,
                    color=ft.Colors.with_opacity(0.12, indicator_color),
                    offset=ft.Offset(0, 3),
                )
                if is_hovered
                else None
            )
            self.update()

        self.on_hover = on_hover


def create_tasks_tab(session_config: dict, save_session_config, refresh_all):
    """Создаёт и возвращает содержимое вкладки «Задачи», включая фильтр-чипы и переключатель Список / Канбан."""
    search_field = ft.TextField(
        hint_text="Поиск задач (Cmd+F)...",
        prefix_icon=ft.Icons.SEARCH_ROUNDED,
        expand=True,
        text_size=12,
        height=38,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=0),
        border_radius=10,
        border_color=BG_CARD_BORDER,
        focused_border_color=COLOR_PRIMARY,
        on_change=lambda e: refresh_all(),
    )

    filter_status = ft.Dropdown(
        label="Статус",
        value=session_config.get("filter_status", FILTER_ALL),
        options=[
            ft.dropdown.Option(FILTER_ALL),
            ft.dropdown.Option(STATUS_TODO),
            ft.dropdown.Option(STATUS_DOING),
            ft.dropdown.Option(STATUS_DONE),
        ],
        width=135,
        text_size=12,
        border_radius=10,
        border_color=BG_CARD_BORDER,
        focused_border_color=COLOR_PRIMARY,
        dense=True,
        on_change=lambda e: (save_session_config(), refresh_all()),
    )

    filter_tag = ft.Dropdown(
        label="Тег",
        value=session_config.get("filter_tag", FILTER_ALL_TAGS),
        options=[ft.dropdown.Option(FILTER_ALL_TAGS)],
        width=135,
        text_size=12,
        border_radius=10,
        border_color=BG_CARD_BORDER,
        focused_border_color=COLOR_PRIMARY,
        dense=True,
        on_change=lambda e: (save_session_config(), refresh_all()),
    )

    sort_dropdown = ft.Dropdown(
        label="Сортировка",
        value=session_config.get("sort_by", SORT_PRIORITY),
        options=[
            ft.dropdown.Option(SORT_PRIORITY),
            ft.dropdown.Option(SORT_DEADLINE),
            ft.dropdown.Option(SORT_EFFORT),
            ft.dropdown.Option(SORT_SUBJECT),
        ],
        width=175,
        text_size=12,
        border_radius=10,
        border_color=BG_CARD_BORDER,
        focused_border_color=COLOR_PRIMARY,
        dense=True,
        on_change=lambda e: (save_session_config(), refresh_all()),
    )

    # Быстрые фильтры-чипы
    active_chip = [CHIP_ALL]
    chips_data = [
        (CHIP_ALL, ft.Icons.ALL_INBOX_ROUNDED),
        (CHIP_URGENT, ft.Icons.LOCAL_FIRE_DEPARTMENT_ROUNDED),
        (CHIP_TODAY, ft.Icons.TODAY_ROUNDED),
        (CHIP_OVERDUE, ft.Icons.WARNING_AMBER_ROUNDED),
        (CHIP_EXAMS, ft.Icons.SCHOOL_ROUNDED),
        (CHIP_DONE, ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED),
    ]

    chip_buttons = []

    def set_chip(chip_name: str):
        active_chip[0] = chip_name
        for btn, name in chip_buttons:
            is_sel = name == chip_name
            btn.bgcolor = ft.Colors.with_opacity(0.18, COLOR_PRIMARY) if is_sel else ft.Colors.with_opacity(0.05, ft.Colors.WHITE)
            btn.border = ft.border.all(1, COLOR_PRIMARY if is_sel else BG_CARD_BORDER)
            btn.content.controls[1].color = COLOR_PRIMARY if is_sel else ft.Colors.GREY_300
            btn.content.controls[1].weight = ft.FontWeight.BOLD if is_sel else ft.FontWeight.W_500
        refresh_all()

    for name, icon in chips_data:
        is_selected = name == active_chip[0]
        btn = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, size=13, color=COLOR_PRIMARY if is_selected else ft.Colors.GREY_400),
                    ft.Text(name, size=11, weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.W_500, color=COLOR_PRIMARY if is_selected else ft.Colors.GREY_300),
                ],
                spacing=4,
                tight=True,
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.18, COLOR_PRIMARY) if is_selected else ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
            border=ft.border.all(1, COLOR_PRIMARY if is_selected else BG_CARD_BORDER),
            on_click=lambda e, n=name: set_chip(n),
            animate=100,
        )
        chip_buttons.append((btn, name))

    chips_row = ft.Row(
        [b[0] for b in chip_buttons],
        wrap=True,
        spacing=6,
        run_spacing=4,
    )

    # Переключатель режимов отображения (Список / Канбан)
    view_mode = [session_config.get("view_mode", "list")]

    def toggle_view_mode(mode: str):
        view_mode[0] = mode
        session_config["view_mode"] = mode
        save_session_config()
        btn_list.bgcolor = ft.Colors.with_opacity(0.2, COLOR_PRIMARY) if mode == "list" else ft.Colors.TRANSPARENT
        btn_kanban.bgcolor = ft.Colors.with_opacity(0.2, COLOR_PRIMARY) if mode == "kanban" else ft.Colors.TRANSPARENT
        btn_list.update()
        btn_kanban.update()
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
    is_dark: bool = True,
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
        _render_kanban_view(sorted_tasks, db, refresh_all, open_edit_dialog, open_delete_confirm, tasks_view, is_dark=is_dark)
    else:
        _render_list_view(sorted_tasks, db, refresh_all, open_edit_dialog, open_delete_confirm, task_list, tasks_view, is_dark=is_dark)


def _render_list_view(sorted_tasks, db, refresh_all, open_edit_dialog, open_delete_confirm, task_list, tasks_view, is_dark: bool = True):
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
                new_controls.append(TaskCard(t, db, refresh_all, open_edit_dialog, open_delete_confirm, is_dark=is_dark))

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


def _render_kanban_view(sorted_tasks, db, refresh_all, open_edit_dialog, open_delete_confirm, tasks_view, is_dark: bool = True):
    """Отрисовывает задачи в виде 3 интерактивных колонок Канбан-доски с адаптивными карточками."""
    if not tasks_view or not hasattr(tasks_view, "kanban_container"):
        return

    kanban_container = tasks_view.kanban_container
    tasks_view.content_area.content = kanban_container
    palette = get_theme_palette(is_dark)

    todo_tasks = [t for t in sorted_tasks if t.status == TaskStatus.TODO]
    doing_tasks = [t for t in sorted_tasks if t.status == TaskStatus.DOING]
    done_tasks = [t for t in sorted_tasks if t.status == TaskStatus.DONE]

    def build_column(title, count, tasks, color, icon, target_status):
        card_items = []
        if not tasks:
            card_items.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.INBOX_ROUNDED, size=28, color=palette["text_muted"]),
                            ft.Text("Нет задач", size=12, color=palette["text_muted"], weight=ft.FontWeight.W_500),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4,
                    ),
                    padding=30,
                    alignment=ft.alignment.center,
                    border=ft.border.all(1, ft.Colors.with_opacity(0.15, palette["bg_card_border"])),
                    border_radius=10,
                )
            )
        else:
            for t in tasks:
                card_items.append(KanbanCard(t, db, refresh_all, open_edit_dialog, open_delete_confirm, is_dark=is_dark))

        col_content = ft.ListView(
            card_items,
            spacing=8,
            expand=True,
            padding=ft.padding.only(right=4),
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
                                        ft.Text(title, size=13, weight=ft.FontWeight.BOLD, color=palette["text_primary"]),
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
                        bgcolor=palette["bg_card"],
                        border=ft.border.all(1, palette["bg_card_border"]),
                    ),
                    ft.Container(
                        content=col_content,
                        expand=True,
                    ),
                ],
                spacing=8,
                expand=True,
            ),
            bgcolor=ft.Colors.with_opacity(0.04, palette["text_primary"]),
            border_radius=12,
            border=ft.border.all(1, palette["bg_card_border"]),
            padding=10,
            expand=True,
        )

    kanban_container.controls = [
        build_column("К выполнению", len(todo_tasks), todo_tasks, COLOR_PRIMARY, ft.Icons.FORMAT_LIST_BULLETED_ROUNDED, TaskStatus.TODO),
        build_column("В процессе", len(doing_tasks), doing_tasks, COLOR_WARNING, ft.Icons.BOLT_ROUNDED, TaskStatus.DOING),
        build_column("Выполнено", len(done_tasks), done_tasks, COLOR_SUCCESS, ft.Icons.CHECK_CIRCLE_ROUNDED, TaskStatus.DONE),
    ]
