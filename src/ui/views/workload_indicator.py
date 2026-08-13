from datetime import date

import flet as ft

from src.core.config import DAILY_LOAD_LIMIT
from src.ui.constants import (
    BG_CARD,
    BG_CARD_BORDER,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_WARNING,
)


def create_workload_indicator(db):
    """Создаёт стильный виджет дневной нагрузки в стиле macOS."""
    load_label = ft.Text(
        f"Дневная нагрузка: 0 / {DAILY_LOAD_LIMIT} ед.",
        size=13,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    load_percent_text = ft.Text(
        "0%",
        size=12,
        weight=ft.FontWeight.BOLD,
        color=COLOR_SUCCESS,
    )
    load_progress = ft.ProgressBar(
        value=0.0,
        color=COLOR_SUCCESS,
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        height=6,
        border_radius=4,
    )
    warning_banner = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=14, color=COLOR_DANGER),
                ft.Text(
                    f"Нагрузка на сегодня превышает рекомендованный лимит ({DAILY_LOAD_LIMIT} ед.)!",
                    color=COLOR_DANGER,
                    size=12,
                    weight=ft.FontWeight.W_600,
                ),
            ],
            spacing=6,
        ),
        bgcolor=ft.Colors.with_opacity(0.12, COLOR_DANGER),
        padding=ft.padding.symmetric(horizontal=10, vertical=6),
        border_radius=8,
        visible=False,
    )

    load_container = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.BOLT_ROUNDED, size=16, color=COLOR_PRIMARY),
                                load_label,
                            ],
                            spacing=6,
                        ),
                        load_percent_text,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                load_progress,
                warning_banner,
            ],
            spacing=6,
        ),
        padding=ft.padding.symmetric(horizontal=14, vertical=10),
        border_radius=12,
        bgcolor=BG_CARD,
        border=ft.border.all(1, BG_CARD_BORDER),
    )

    def update_load_indicator():
        today_str = date.today().isoformat()
        try:
            load, is_overloaded = db.get_daily_load_for_date(today_str)
        except Exception:
            load, is_overloaded = 0, False

        val = min(1.0, load / DAILY_LOAD_LIMIT) if DAILY_LOAD_LIMIT > 0 else 0.0
        load_progress.value = val
        percent = int(val * 100) if not is_overloaded else int((load / DAILY_LOAD_LIMIT) * 100)
        load_label.value = f"Дневная нагрузка: {load} / {DAILY_LOAD_LIMIT} ед."
        load_percent_text.value = f"{percent}%"

        if is_overloaded:
            load_progress.color = COLOR_DANGER
            load_percent_text.color = COLOR_DANGER
            warning_banner.visible = True
        elif val >= 0.8:
            load_progress.color = COLOR_WARNING
            load_percent_text.color = COLOR_WARNING
            warning_banner.visible = False
        else:
            load_progress.color = COLOR_SUCCESS
            load_percent_text.color = COLOR_SUCCESS
            warning_banner.visible = False

    return load_container, update_load_indicator
