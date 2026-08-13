import flet as ft

from src.ui.constants import get_theme_palette


def create_kpi_card(
    title: str,
    value: str,
    icon: str,
    color: str,
    subtitle: str = "",
    is_dark: bool = True,
) -> ft.Container:
    """Создаёт премиальную KPI-карточку в стиле macOS с акцентной иконкой, темой и hover-анимацией."""
    palette = get_theme_palette(is_dark)

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
                            color=palette["text_secondary"],
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
                    color=palette["text_primary"],
                ),
                *(
                    [
                        ft.Text(
                            subtitle,
                            size=10,
                            color=palette["text_muted"],
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
        bgcolor=palette["bg_card"],
        border=ft.border.all(1, palette["bg_card_border"]),
        border_radius=12,
        padding=ft.padding.symmetric(horizontal=14, vertical=12),
        expand=True,
        scale=1.0,
        animate_scale=150,
    )

    def on_hover(e):
        is_hovered = e.data == "true"
        e.control.scale = 1.025 if is_hovered else 1.0
        e.control.bgcolor = palette["bg_card_hover"] if is_hovered else palette["bg_card"]
        e.control.border = ft.border.all(
            1,
            ft.Colors.with_opacity(0.4, color) if is_hovered else palette["bg_card_border"],
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
