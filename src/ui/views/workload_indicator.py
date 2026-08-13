from datetime import date

import flet as ft

from src.core.config import DAILY_LOAD_LIMIT
from src.ui.constants import BG_CARD


def create_workload_indicator(db):
    """Создаёт виджет дневной нагрузки и возвращает (load_container, update_load_indicator_func)."""
    load_label = ft.Text(
        f"Дневная нагрузка на сегодня: 0 / {DAILY_LOAD_LIMIT}",
        size=15,
        weight=ft.FontWeight.W_600,
        color=ft.Colors.LIGHT_BLUE_100,
    )
    load_progress = ft.ProgressBar(
        value=0.0,
        color=ft.Colors.GREEN_ACCENT,
        bgcolor=ft.Colors.GREY_800,
        height=8,
        border_radius=4,
    )
    warning_banner = ft.Text(
        "",
        color=ft.Colors.RED_ACCENT,
        size=13,
        weight=ft.FontWeight.BOLD,
        visible=False,
    )

    load_container = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.AUTO_AWESOME, size=16, color=ft.Colors.AMBER),
                        load_label,
                    ],
                    spacing=6,
                ),
                load_progress,
                warning_banner,
            ],
            spacing=8,
        ),
        padding=15,
        border_radius=12,
        bgcolor=BG_CARD,
        border=ft.border.all(1, ft.Colors.GREY_800),
    )

    def update_load_indicator():
        today_str = date.today().isoformat()
        try:
            load, is_overloaded = db.get_daily_load_for_date(today_str)
        except Exception:
            load, is_overloaded = 0, False

        val = min(1.0, load / DAILY_LOAD_LIMIT) if DAILY_LOAD_LIMIT > 0 else 0.0
        load_progress.value = val
        load_label.value = f"Дневная нагрузка на сегодня: {load} / {DAILY_LOAD_LIMIT} ед."

        if is_overloaded:
            load_progress.color = ft.Colors.RED_ACCENT
            warning_banner.value = f"⚠️ Дневная нагрузка на сегодня превышает рекомендованный лимит ({DAILY_LOAD_LIMIT} ед.)!"
            warning_banner.visible = True
        elif val >= 0.8:
            load_progress.color = ft.Colors.AMBER_ACCENT
            warning_banner.visible = False
        else:
            load_progress.color = ft.Colors.GREEN_ACCENT
            warning_banner.visible = False

    return load_container, update_load_indicator
