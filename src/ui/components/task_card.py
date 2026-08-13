from datetime import date

import flet as ft

from src.core.logic import calculate_priority
from src.core.models import Task, TaskStatus
from src.ui.constants import (
    BG_CARD,
    BG_CARD_BORDER,
    BG_CARD_HOVER,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_WARNING,
)


class TaskCard(ft.Container):
    """Премиальный компонент карточки задачи в стиле macOS с бейджем обратного отсчета и hover-эффектом."""

    def __init__(self, task: Task, db, trigger_data_update, open_edit_dialog, open_delete_confirm):
        super().__init__()
        self.task = task
        self.db = db
        self.trigger_data_update = trigger_data_update
        self.open_edit_dialog = open_edit_dialog
        self.open_delete_confirm = open_delete_confirm

        self.key = f"task_{self.task.id}" if self.task.id is not None else None
        self.padding = ft.padding.symmetric(horizontal=16, vertical=12)
        self.border_radius = 12
        self.bgcolor = BG_CARD
        self.scale = 1.0
        self.animate_scale = 150
        self.on_hover = self.card_hover

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

    def _get_deadline_badge(self) -> ft.Container:
        """Генерирует бейдж человекочитаемого обратного отсчета до дедлайна."""
        try:
            deadline_date = date.fromisoformat(self.task.deadline)
            today = date.today()
            delta_days = (deadline_date - today).days

            if self.task.status == TaskStatus.DONE:
                text = f"Завершено ({self.task.deadline})"
                bg = ft.Colors.with_opacity(0.12, COLOR_SUCCESS)
                color = COLOR_SUCCESS
                icon = ft.Icons.CHECK_CIRCLE_OUTLINE
            elif delta_days < 0:
                text = f"Просрочено на {-delta_days} дн."
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
            elif delta_days <= 3:
                text = f"Через {delta_days} дн."
                bg = ft.Colors.with_opacity(0.12, COLOR_WARNING)
                color = COLOR_WARNING
                icon = ft.Icons.CALENDAR_TODAY
            else:
                text = f"До {self.task.deadline}"
                bg = ft.Colors.with_opacity(0.08, ft.Colors.BLUE_GREY)
                color = ft.Colors.GREY_400
                icon = ft.Icons.CALENDAR_MONTH_OUTLINED
        except Exception:
            text = self.task.deadline
            bg = ft.Colors.with_opacity(0.08, ft.Colors.BLUE_GREY)
            color = ft.Colors.GREY_400
            icon = ft.Icons.CALENDAR_MONTH_OUTLINED

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, size=11, color=color),
                    ft.Text(text, size=11, color=color, weight=ft.FontWeight.W_600),
                ],
                spacing=4,
                tight=True,
            ),
            bgcolor=bg,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=8,
        )

    def build_ui(self):
        indicator_color = self._get_indicator_color()

        self.border = ft.Border(
            left=ft.BorderSide(4, indicator_color),
            top=ft.BorderSide(1, BG_CARD_BORDER),
            right=ft.BorderSide(1, BG_CARD_BORDER),
            bottom=ft.BorderSide(1, BG_CARD_BORDER),
        )

        is_done = self.task.status == TaskStatus.DONE
        is_doing = self.task.status == TaskStatus.DOING
        text_decor = ft.TextDecoration.LINE_THROUGH if is_done else None
        text_color = ft.Colors.GREY_400 if is_done else ft.Colors.WHITE
        desc_color = ft.Colors.GREY_500 if is_done else ft.Colors.GREY_300

        # Статусный бейдж
        if is_done:
            status_badge = ft.Container(
                content=ft.Text("✅ Готово", size=10, color=COLOR_SUCCESS, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.with_opacity(0.12, COLOR_SUCCESS),
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                border_radius=6,
            )
        elif is_doing:
            status_badge = ft.Container(
                content=ft.Text("⚡ В процессе", size=10, color=COLOR_WARNING, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.with_opacity(0.15, COLOR_WARNING),
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                border_radius=6,
            )
        else:
            status_badge = ft.Container(
                content=ft.Text("📝 Сделать", size=10, color=COLOR_PRIMARY, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.with_opacity(0.12, COLOR_PRIMARY),
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                border_radius=6,
            )

        tags_ui = [status_badge]
        for t in self.task.tags:
            is_exam = t in ("ОГЭ", "ЕГЭ", "Экзамен")
            tag_color = COLOR_DANGER if is_exam else ft.Colors.BLUE_GREY_200
            tag_bg = (
                ft.Colors.with_opacity(0.15, COLOR_DANGER)
                if is_exam
                else ft.Colors.with_opacity(0.1, ft.Colors.BLUE_GREY)
            )
            tags_ui.append(
                ft.Container(
                    content=ft.Text(f"#{t}", size=10, color=tag_color, weight=ft.FontWeight.W_600),
                    bgcolor=tag_bg,
                    padding=ft.padding.symmetric(horizontal=6, vertical=3),
                    border_radius=6,
                )
            )

        status_dropdown = [
            ft.Container(
                content=ft.Dropdown(
                    value=str(self.task.status.value),
                    options=[
                        ft.dropdown.Option("0", "📝 Сделать"),
                        ft.dropdown.Option("1", "⚡ В процессе"),
                        ft.dropdown.Option("2", "✅ Готово"),
                    ],
                    width=135,
                    text_size=11,
                    content_padding=ft.padding.symmetric(horizontal=8, vertical=0),
                    border_radius=8,
                    border_color=ft.Colors.with_opacity(0.4, indicator_color),
                    on_change=self._on_status_change,
                ),
                height=38,
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
                        width=120,
                        text_size=11,
                        label_style=ft.TextStyle(size=10),
                        content_padding=ft.padding.symmetric(horizontal=8, vertical=0),
                        border_radius=8,
                        border_color=ft.Colors.with_opacity(0.4, COLOR_SUCCESS),
                        on_change=self._on_grade_change,
                    ),
                    height=38,
                    width=120,
                )
            ]

        self.content = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    expand=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Checkbox(
                            value=is_done,
                            on_change=self.toggle_task_status,
                            fill_color={
                                ft.ControlState.SELECTED: COLOR_SUCCESS,
                                ft.ControlState.DEFAULT: ft.Colors.GREY_600,
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
                                            size=15,
                                            color=text_color,
                                            style=ft.TextStyle(decoration=text_decor),
                                        ),
                                        *tags_ui,
                                    ],
                                    wrap=True,
                                    spacing=6,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
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
                                        self._get_deadline_badge(),
                                        ft.Container(
                                            content=ft.Row(
                                                [
                                                    ft.Icon(ft.Icons.BOLT, size=11, color=COLOR_WARNING),
                                                    ft.Text(
                                                        f"Сложность: {self.task.effort_score}",
                                                        size=11,
                                                        color=COLOR_WARNING,
                                                        weight=ft.FontWeight.W_600,
                                                    ),
                                                ],
                                                spacing=3,
                                                tight=True,
                                            ),
                                            bgcolor=ft.Colors.with_opacity(0.1, COLOR_WARNING),
                                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                            border_radius=8,
                                        ),
                                        ft.Container(
                                            content=ft.Row(
                                                [
                                                    ft.Icon(ft.Icons.TRENDING_UP, size=11, color=COLOR_PRIMARY),
                                                    ft.Text(
                                                        f"Приоритет: {self.priority:.2f}",
                                                        size=11,
                                                        color=COLOR_PRIMARY,
                                                        weight=ft.FontWeight.W_600,
                                                    ),
                                                ],
                                                spacing=3,
                                                tight=True,
                                            ),
                                            bgcolor=ft.Colors.with_opacity(0.1, COLOR_PRIMARY),
                                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                            border_radius=8,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.START,
                                    spacing=6,
                                    wrap=True,
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
                            icon_color=COLOR_PRIMARY,
                            icon_size=18,
                            tooltip="Редактировать задачу",
                            on_click=lambda e: self.open_edit_dialog(self.task),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                            icon_color=COLOR_DANGER,
                            icon_size=18,
                            tooltip="Удалить задачу",
                            on_click=lambda e: self.open_delete_confirm(self.task.id, self.task.subject),
                        ),
                    ],
                    spacing=4,
                ),
            ],
        )

    def card_hover(self, e):
        indicator_color = self._get_indicator_color()
        is_hovered = e.data == "true"
        self.scale = 1.012 if is_hovered else 1.0
        self.bgcolor = BG_CARD_HOVER if is_hovered else BG_CARD
        self.shadow = (
            ft.BoxShadow(
                blur_radius=12,
                color=ft.Colors.with_opacity(0.12, indicator_color),
                offset=ft.Offset(0, 4),
            )
            if is_hovered
            else None
        )
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
