import flet as ft

from src.ui.constants import (
    BG_CARD,
    BG_CARD_BORDER,
    COLOR_PRIMARY,
    COLOR_WARNING,
)


def create_shortcuts_dialog(page: ft.Page) -> ft.AlertDialog:
    """Создаёт стильное модальное окно справки по горячим клавишам macOS."""
    shortcuts = [
        ("Cmd + N", "Создать новую задачу", ft.Icons.ADD_CIRCLE_OUTLINE, COLOR_PRIMARY),
        ("Cmd + F", "Фокус на строке поиска", ft.Icons.SEARCH_ROUNDED, COLOR_PRIMARY),
        ("Cmd + R", "Принудительно обновить данные", ft.Icons.REFRESH_ROUNDED, COLOR_PRIMARY),
        ("Cmd + T", "Переключить тему (Тёмная / Светлая)", ft.Icons.DARK_MODE_OUTLINED, COLOR_WARNING),
        ("Cmd + 1..4", "Быстрое переключение вкладок", ft.Icons.TAB_ROUNDED, COLOR_PRIMARY),
        ("Cmd + /", "Открыть эту справку горячих клавиш", ft.Icons.HELP_OUTLINE_ROUNDED, COLOR_PRIMARY),
    ]

    rows = []
    for key, desc, icon, color in shortcuts:
        rows.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Icon(icon, size=16, color=color),
                                ft.Text(desc, size=13, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500),
                            ],
                            spacing=8,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Text(key, size=12, color=COLOR_PRIMARY, weight=ft.FontWeight.BOLD),
                            bgcolor=ft.Colors.with_opacity(0.12, COLOR_PRIMARY),
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            border_radius=6,
                            border=ft.border.all(1, ft.Colors.with_opacity(0.3, COLOR_PRIMARY)),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                bgcolor=BG_CARD,
                border_radius=8,
                border=ft.border.all(1, BG_CARD_BORDER),
            )
        )

    dialog = ft.AlertDialog(
        title=ft.Row(
            [
                ft.Icon(ft.Icons.KEYBOARD_ROUNDED, color=COLOR_PRIMARY, size=22),
                ft.Text("Горячие клавиши (macOS)", size=17, weight=ft.FontWeight.BOLD),
            ],
            spacing=8,
        ),
        content=ft.Container(
            content=ft.Column(rows, spacing=8, tight=True),
            width=460,
        ),
        actions=[
            ft.TextButton("Понятно", on_click=lambda e: page.close(dialog)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    return dialog
