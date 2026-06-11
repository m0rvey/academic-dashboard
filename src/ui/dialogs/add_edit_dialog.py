from datetime import date, datetime

import flet as ft

from src.core.config import MAX_EFFORT, MIN_EFFORT
from src.core.models import Task, TaskStatus


def create_add_edit_dialog(page: ft.Page, db, show_snack, refresh_all):
    """Создаёт и возвращает диалог добавления/редактирования задачи и функции открытия."""
    editing_task_id = None

    subject_field = ft.TextField(
        label="Предмет (например: Математика)",
        autofocus=True,
        border_color=ft.Colors.GREY_700,
        on_change=lambda e: clear_field_error(subject_field),
    )
    desc_field = ft.TextField(
        label="Описание задачи",
        multiline=True,
        min_lines=2,
        border_color=ft.Colors.GREY_700,
        on_change=lambda e: clear_field_error(desc_field),
    )
    tags_field = ft.TextField(label="Теги (через запятую)", border_color=ft.Colors.GREY_700)

    effort_slider = ft.Slider(
        min=MIN_EFFORT,
        max=MAX_EFFORT,
        divisions=MAX_EFFORT - MIN_EFFORT,
        label="{value}",
        value=MIN_EFFORT,
        on_change=lambda e: update_slider_label(e),
    )
    effort_label = ft.Text(f"Сложность: {MIN_EFFORT} (Очень легко)", color=ft.Colors.GREY_400, size=13)

    def update_slider_label(e):
        val = int(effort_slider.value)
        labels = {
            1: "1 - Очень легко",
            2: "2 - Легко",
            3: "3 - Просто",
            4: "4 - Ниже среднего",
            5: "5 - Средне",
            6: "6 - Выше среднего",
            7: "7 - Сложно",
            8: "8 - Довольно сложно",
            9: "9 - Очень сложно",
            10: "10 - Экстремально сложно",
        }
        effort_label.value = f"Сложность: {labels.get(val, str(val))}"
        page.update()

    def clear_field_error(field):
        if field.error_text:
            field.error_text = None
            field.border_color = ft.Colors.GREY_700
            page.update()

    def date_changed(e):
        if date_picker.value:
            deadline_btn.text = date_picker.value.strftime("%Y-%m-%d")
        else:
            deadline_btn.text = date.today().isoformat()
        page.update()

    date_picker = ft.DatePicker(on_change=date_changed)

    def open_date_picker(e):
        if date_picker not in page.overlay:
            page.overlay.append(date_picker)
            page.update()
        page.open(date_picker)

    deadline_btn = ft.ElevatedButton(
        text=date.today().isoformat(),
        icon=ft.Icons.CALENDAR_MONTH_ROUNDED,
        on_click=open_date_picker,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
    )

    active_dialog = None

    def save_task(e):
        nonlocal editing_task_id
        subject = subject_field.value.strip()
        description = desc_field.value.strip()

        has_error = False
        if not subject:
            subject_field.error_text = "Предмет не может быть пустым!"
            subject_field.border_color = ft.Colors.RED_ACCENT
            has_error = True
        if not description:
            desc_field.error_text = "Описание не может быть пустым!"
            desc_field.border_color = ft.Colors.RED_ACCENT
            has_error = True

        if has_error:
            page.update()
            return

        tags_str = tags_field.value.strip()
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        deadline = deadline_btn.text
        effort = int(effort_slider.value)

        task = Task(
            subject=subject,
            description=description,
            deadline=deadline,
            effort_score=effort,
            tags=tags,
            status=TaskStatus.TODO,
        )

        if editing_task_id is not None:
            task.id = editing_task_id
            old_task = next((t for t in db.get_all_tasks() if t.id == task.id), None)
            if old_task:
                task.status = old_task.status
                task.grade = old_task.grade
            db.update_task(task)
            show_snack("✅ Задача успешно обновлена!")
        else:
            db.add_task(task)
            show_snack("✅ Задача успешно добавлена!")

        if active_dialog:
            page.close(active_dialog)
        refresh_all()

    def build_dialog(title_text: str):
        nonlocal active_dialog
        active_dialog = ft.AlertDialog(
            title=ft.Text(title_text, weight=ft.FontWeight.BOLD),
            content=ft.Column(
                [
                    subject_field,
                    desc_field,
                    ft.Row(
                        [ft.Text("Дедлайн:", weight=ft.FontWeight.W_500), deadline_btn],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(color=ft.Colors.GREY_800),
                    effort_label,
                    effort_slider,
                    tags_field,
                ],
                tight=True,
                spacing=12,
                width=420,
            ),
            actions=[
                ft.TextButton("Отмена", on_click=lambda e: page.close(active_dialog)),
                ft.ElevatedButton(
                    "Сохранить",
                    bgcolor=ft.Colors.LIGHT_BLUE_600,
                    color=ft.Colors.WHITE,
                    on_click=save_task,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        return active_dialog

    def open_edit_dialog(task: Task):
        nonlocal editing_task_id
        editing_task_id = task.id
        subject_field.value = task.subject
        subject_field.error_text = None
        subject_field.border_color = ft.Colors.GREY_700

        desc_field.value = task.description
        desc_field.error_text = None
        desc_field.border_color = ft.Colors.GREY_700

        try:
            deadline_date = datetime.strptime(task.deadline[:10], "%Y-%m-%d")
        except (ValueError, TypeError, IndexError):
            deadline_date = datetime.today()

        date_picker.value = deadline_date
        deadline_btn.text = deadline_date.strftime("%Y-%m-%d")

        effort_slider.value = float(max(MIN_EFFORT, min(MAX_EFFORT, task.effort_score)))
        update_slider_label(None)

        tags_field.value = ", ".join(task.tags)

        dialog = build_dialog("Редактировать задачу")
        page.open(dialog)

    def open_add_dialog(e):
        nonlocal editing_task_id
        editing_task_id = None
        subject_field.value = ""
        subject_field.error_text = None
        subject_field.border_color = ft.Colors.GREY_700

        desc_field.value = ""
        desc_field.error_text = None
        desc_field.border_color = ft.Colors.GREY_700

        tags_field.value = ""
        effort_slider.value = float(MIN_EFFORT)
        update_slider_label(None)

        today_dt = datetime.today()
        date_picker.value = today_dt
        deadline_btn.text = today_dt.strftime("%Y-%m-%d")

        dialog = build_dialog("Добавить новую задачу")
        page.open(dialog)

    return None, open_add_dialog, open_edit_dialog
