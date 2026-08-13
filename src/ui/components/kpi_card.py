import flet as ft

from src.ui.constants import BG_CARD, BG_CARD_BORDER, BG_CARD_HOVER


def create_kpi_card(title: str, value: str, icon: str, color: str, subtitle: str = "") -> ft.Container:
    """Создаёт премиальную KPI-карточку в стиле macOS с акцентной иконкой и hover-анимацией."""
    icon_container = ft.Container(
        content=ft.Icon(icon, size=18, color=color),
        bgcolor=ft.Colors.with_opacity(0.12, color),
        border_radius=8,
        padding=ft.padding.all(8),
    )

    card = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        icon_container,
                        ft.Text(
                            title,
                            size=12,
                            color=ft.Colors.GREY_400,
                            weight=ft.FontWeight.W_600,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            expand=True,
                        ),
                    ],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(
                    value,
                    size=22,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
                *(
                    [
                        ft.Text(
                            subtitle,
                            size=10,
                            color=ft.Colors.GREY_500,
                            weight=ft.FontWeight.W_500,
                        )
                    ]
                    if subtitle
                    else []
                ),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=BG_CARD,
        border=ft.border.all(1, BG_CARD_BORDER),
        border_radius=12,
        padding=ft.padding.symmetric(horizontal=14, vertical=12),
        expand=True,
        scale=1.0,
        animate_scale=150,
    )

    def on_hover(e):
        is_hovered = e.data == "true"
        e.control.scale = 1.025 if is_hovered else 1.0
        e.control.bgcolor = BG_CARD_HOVER if is_hovered else BG_CARD
        e.control.border = ft.border.all(
            1,
            ft.Colors.with_opacity(0.4, color) if is_hovered else BG_CARD_BORDER,
        )
        e.control.shadow = (
            ft.BoxShadow(
                blur_radius=12,
                color=ft.Colors.with_opacity(0.12, color),
                offset=ft.Offset(0, 4),
            )
            if is_hovered
            else None
        )
        e.control.update()

    card.on_hover = on_hover
    return card
