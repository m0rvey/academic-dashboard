import flet as ft

from src.core.config import LOG_FILE_PATH


def show_debug_console(page: ft.Page) -> None:
    """Создаёт и открывает модальное окно просмотра логов и консоли отладки."""
    log_text_field = ft.TextField(
        value="Загрузка логов...",
        multiline=True,
        read_only=True,
        text_size=11,
        font_family="Courier New",
        height=450,
        width=750,
        border_color=ft.Colors.GREY_800,
        border_radius=8,
        bgcolor=ft.Colors.BLACK,
        color=ft.Colors.GREEN_300,
    )

    def load_logs():
        if not LOG_FILE_PATH.exists():
            log_text_field.value = "Лог-файл ещё не создан или пуст."
        else:
            try:
                with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    last_lines = lines[-150:]
                    log_text_field.value = "".join(last_lines)
            except Exception as ex:
                log_text_field.value = f"Ошибка чтения логов: {ex}"
        try:
            page.update()
        except Exception:
            pass

    def clear_logs(ev):
        try:
            if LOG_FILE_PATH.exists():
                with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
                    f.truncate(0)
            load_logs()
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"❌ Ошибка очистки логов: {ex}")))

    debug_dialog = ft.AlertDialog(
        title=ft.Row(
            [
                ft.Icon(ft.Icons.TERMINAL_ROUNDED, color=ft.Colors.LIGHT_BLUE_200),
                ft.Text("Консоль отладки и логи", size=18, weight=ft.FontWeight.BOLD),
            ],
            spacing=10,
        ),
        content=ft.Column(
            [
                log_text_field,
            ],
            tight=True,
        ),
        actions=[
            ft.TextButton("Обновить", on_click=lambda ev: load_logs(), icon=ft.Icons.REFRESH_ROUNDED),
            ft.TextButton("Очистить", on_click=clear_logs, icon=ft.Icons.DELETE_ROUNDED, icon_color=ft.Colors.RED_ACCENT),
            ft.TextButton("Закрыть", on_click=lambda ev: page.close(debug_dialog)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.open(debug_dialog)
    load_logs()
