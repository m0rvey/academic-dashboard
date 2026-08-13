import flet as ft

from src.core.logic import calculate_priority
from src.core.models import Task, TaskStatus
from src.ui.constants import BG_CARD, BG_CARD_HOVER


class TaskCard(ft.Container):
    """ООП-компонент карточки задачи для оптимизации памяти и точечного рендеринга."""

    def __init__(self, task: Task, db, trigger_data_update, open_edit_dialog, open_delete_confirm):
        super().__init__()
        self.task = task
        self.db = db
        self.trigger_data_update = trigger_data_update
        self.open_edit_dialog = open_edit_dialog
        self.open_delete_confirm = open_delete_confirm

        self.key = f"task_{self.task.id}" if self.task.id is not None else None
        self.padding = 12
        self.border_radius = 10
        self.bgcolor = BG_CARD
        self.scale = 1.0
        self.animate_scale = 150
        self.on_hover = self.card_hover

        self.priority = calculate_priority(self.task)
        self.build_ui()

    def _get_indicator_color(self):
        if self.task.status == TaskStatus.DONE:
            return ft.Colors.GREY_500
        elif self.task.status == TaskStatus.DOING:
            return ft.Colors.AMBER_400
        elif self.priority >= 2.5:
            return ft.Colors.RED_ACCENT_400
        elif self.priority >= 1.5:
            return ft.Colors.AMBER_400
        return ft.Colors.TEAL_400

    def build_ui(self):
        indicator_color = self._get_indicator_color()

        self.border = ft.Border(
            left=ft.BorderSide(4, indicator_color),
            top=ft.BorderSide(1, ft.Colors.GREY_800),
            right=ft.BorderSide(1, ft.Colors.GREY_800),
            bottom=ft.BorderSide(1, ft.Colors.GREY_800),
        )

        is_done = self.task.status == TaskStatus.DONE
        is_doing = self.task.status == TaskStatus.DOING
        text_decor = ft.TextDecoration.LINE_THROUGH if is_done else None
        text_color = ft.Colors.GREY_400 if is_done else ft.Colors.WHITE
        desc_color = ft.Colors.GREY_600 if is_done else ft.Colors.GREY_300

        # Отображение статуса задачи
        if is_done:
            status_badge = ft.Container(
                content=ft.Text("✅ Готово", size=10, color=ft.Colors.GREEN_100, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.GREEN_900,
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                border_radius=10,
            )
        elif is_doing:
            status_badge = ft.Container(
                content=ft.Text("⚡ В процессе", size=10, color=ft.Colors.AMBER_100, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.AMBER_900,
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                border_radius=10,
            )
        else:
            status_badge = ft.Container(
                content=ft.Text("📝 TODO", size=10, color=ft.Colors.GREY_300, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.GREY_800,
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                border_radius=10,
            )

        tags_ui = [status_badge]
        for t in self.task.tags:
            tags_ui.append(
                ft.Container(
                    content=ft.Text(t, size=10, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                    bgcolor=ft.Colors.BLUE_900 if not is_done else ft.Colors.GREY_800,
                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                    border_radius=10,
                )
            )

        status_dropdown = [
            ft.Container(
                content=ft.Dropdown(
                    value=str(self.task.status.value),
                    options=[
                        ft.dropdown.Option("0", "📝 TODO"),
                        ft.dropdown.Option("1", "⚡ В процессе"),
                        ft.dropdown.Option("2", "✅ Готово"),
                    ],
                    width=135,
                    text_size=11,
                    content_padding=ft.padding.symmetric(horizontal=8, vertical=0),
                    border_radius=8,
                    border_color=ft.Colors.AMBER_700 if is_doing else ft.Colors.GREY_800,
                    on_change=self._on_status_change,
                ),
                height=45,
                width=135,
            )
        ]

        grade_dropdown = []
        if is_done:
            grade_dropdown = [
                ft.Container(
                    content=ft.Dropdown(
                        label="Оценка",
                        value=(str(self.task.grade) if self.task.grade is not None else "None"),
                        options=[
                            ft.dropdown.Option("None", "—"),
                            ft.dropdown.Option("5", "5 (Отлично)"),
                            ft.dropdown.Option("4", "4 (Хорошо)"),
                            ft.dropdown.Option("3", "3 (Удовл.)"),
                            ft.dropdown.Option("2", "2 (Неудовл.)"),
                        ],
                        width=130,
                        text_size=12,
                        label_style=ft.TextStyle(size=10),
                        content_padding=ft.padding.symmetric(horizontal=10, vertical=0),
                        border_radius=8,
                        border_color=ft.Colors.GREY_800,
                        on_change=self._on_grade_change,
                    ),
                    height=45,
                    width=130,
                )
            ]

        self.content = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    expand=True,
                    controls=[
                        ft.Checkbox(
                            value=is_done,
                            on_change=self.toggle_task_status,
                            fill_color={
                                ft.ControlState.SELECTED: ft.Colors.LIGHT_BLUE_400,
                                ft.ControlState.DEFAULT: ft.Colors.GREY_400,
                            },
                        ),
                        ft.Column(
                            expand=True,
                            horizontal_alignment=ft.CrossAxisAlignment.START,
                            spacing=4,
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text(
                                            self.task.subject,
                                            weight=ft.FontWeight.BOLD,
                                            size=16,
                                            color=text_color,
                                            style=ft.TextStyle(decoration=text_decor),
                                        ),
                                        *tags_ui,
                                    ],
                                    wrap=True,
                                    spacing=6,
                                ),
                                ft.Text(
                                    self.task.description,
                                    size=13,
                                    color=desc_color,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Row(
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.CALENDAR_MONTH_OUTLINED,
                                            size=12,
                                            color=ft.Colors.GREY_500,
                                        ),
                                        ft.Text(
                                            f"Дедлайн: {self.task.deadline}",
                                            size=11,
                                            color=ft.Colors.GREY_500,
                                        ),
                                        ft.Container(width=10),
                                        ft.Icon(
                                            ft.Icons.SPEED_OUTLINED,
                                            size=12,
                                            color=ft.Colors.GREY_500,
                                        ),
                                        ft.Text(
                                            f"Сложность: {self.task.effort_score}",
                                            size=11,
                                            color=ft.Colors.GREY_500,
                                        ),
                                        ft.Container(width=10),
                                        ft.Icon(
                                            ft.Icons.STAR_OUTLINE,
                                            size=12,
                                            color=ft.Colors.GREY_500,
                                        ),
                                        ft.Text(
                                            f"Приоритет: {self.priority:.2f}",
                                            size=11,
                                            color=ft.Colors.GREY_500,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.START,
                                    spacing=4,
                                ),
                            ],
                        ),
                    ],
                ),
                ft.Row(
                    [
                        *status_dropdown,
                        *grade_dropdown,
                        ft.IconButton(
                            icon=ft.Icons.EDIT_OUTLINED,
                            icon_color=ft.Colors.BLUE_300,
                            tooltip="Редактировать",
                            on_click=lambda e: self.open_edit_dialog(self.task),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINED,
                            icon_color=ft.Colors.RED_300,
                            tooltip="Удалить",
                            on_click=lambda e: self.open_delete_confirm(self.task.id, self.task.subject),
                        ),
                    ],
                    spacing=6,
                ),
            ],
        )

    def card_hover(self, e):
        indicator_color = self._get_indicator_color()
        if e.data == "true":
            self.scale = 1.015
            self.bgcolor = BG_CARD_HOVER
            self.shadow = ft.BoxShadow(
                blur_radius=12,
                color=ft.Colors.with_opacity(0.15, indicator_color),
                offset=ft.Offset(0, 4),
            )
        else:
            self.scale = 1.0
            self.bgcolor = BG_CARD
            self.shadow = None
        self.update()

    def toggle_task_status(self, e):
        new_status = TaskStatus.TODO if self.task.status == TaskStatus.DONE else TaskStatus.DONE
        self.db.update_task_status(self.task.id, new_status)
        self.trigger_data_update()

    def _on_status_change(self, e):
        try:
            new_status_val = int(e.control.value)
            new_status = TaskStatus(new_status_val)
            self.db.update_task_status(self.task.id, new_status)
            self.trigger_data_update()
        except Exception:
            pass

    def _on_grade_change(self, e):
        grade_value = int(e.control.value) if e.control.value != "None" else None
        self.db.update_task_grade(self.task.id, grade_value)
        self.trigger_data_update()

