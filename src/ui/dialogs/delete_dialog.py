import flet as ft

from src.core.logger import setup_logger

logger = setup_logger("delete_dialog")


def create_delete_dialog(page: ft.Page, db, show_snack, refresh_all):
    """Создаёт и возвращает функцию для открытия динамического окна подтверждения удаления задачи."""
    target_delete_id = None

    def open_delete_confirm(task_id: int, task_title: str):
        nonlocal target_delete_id
        target_delete_id = task_id

        dialog = None

        def confirm_delete(e):
            nonlocal target_delete_id
            if target_delete_id is not None:
                try:
                    db.delete_task(target_delete_id)
                    show_snack("🗑 Задача успешно удалена")
                    if dialog:
                        page.close(dialog)
                    refresh_all()
                except Exception as ex:
                    logger.error(f"Error in confirm_delete: {ex}", exc_info=True)
                    if dialog:
                        page.close(dialog)
                    page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Подтверждение удаления", weight=ft.FontWeight.BOLD),
            content=ft.Text(f"Вы уверены, что хотите безвозвратно удалить задачу по предмету '{task_title}'?"),
            actions=[
                ft.TextButton("Отмена", on_click=lambda e: page.close(dialog)),
                ft.ElevatedButton(
                    "Удалить",
                    bgcolor=ft.Colors.RED_600,
                    color=ft.Colors.WHITE,
                    on_click=confirm_delete,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.open(dialog)

    return None, open_delete_confirm
