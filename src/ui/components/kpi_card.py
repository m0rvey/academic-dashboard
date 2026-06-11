import flet as ft

from src.ui.constants import BG_CARD


def create_kpi_card(title: str, value: str, icon: str, color: str) -> ft.Container:
    """Создаёт KPI-карточку с заголовком, значением, иконкой и hover-анимацией."""
    card = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(icon, size=20, color=color),
                        ft.Text(
                            title,
                            size=13,
                            color=ft.Colors.GREY_400,
                            weight=ft.FontWeight.W_500,
                        ),
                    ],
                    spacing=6,
                ),
                ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=BG_CARD,
        border=ft.border.all(1, ft.Colors.GREY_800),
        border_radius=12,
        padding=ft.padding.all(16),
        expand=True,
        alignment=ft.alignment.center,
        scale=1.0,
        animate_scale=100,
    )

    def on_hover(e):
        e.control.scale = 1.05 if e.data == "true" else 1.0
        e.control.update()

    card.on_hover = on_hover
    return card
