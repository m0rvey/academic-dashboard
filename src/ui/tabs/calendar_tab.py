import calendar
from datetime import date, datetime

import flet as ft

from src.core.logger import setup_logger
from src.core.logic import calculate_priority
from src.core.models import TaskStatus, get_clean_date
from src.ui.constants import (
    BG_CARD,
    BG_CARD_BORDER,
    BG_TODAY,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_WARNING,
)

logger = setup_logger("calendar_tab")


def create_calendar_tab(db, page: ft.Page):
    """Создаёт и возвращает содержимое вкладки «Календарь» и функцию обновления сетки."""
    calendar_state = {"year": datetime.today().year, "month": datetime.today().month}

    month_label = ft.Text("", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    calendar_grid_col = ft.Column(spacing=4, expand=True)

    def open_day_dialog(y, m, d):
        date_str = f"{y:04d}-{m:02d}-{d:02d}"
        day_tasks_list = ft.ListView(expand=True, spacing=8, height=220)

        dialog_ref = [None]
        dialog = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.CALENDAR_MONTH_ROUNDED, color=COLOR_PRIMARY, size=20),
                    ft.Text(f"Дедлайн: {d:02d}.{m:02d}.{y}", weight=ft.FontWeight.BOLD, size=16),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column([day_tasks_list], tight=True),
                width=380,
            ),
            actions=[ft.TextButton("Закрыть", on_click=lambda e: page.close(dialog_ref[0]))],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        dialog_ref[0] = dialog

        try:
            day_tasks = db.get_all_tasks_by_date(date_str)
        except Exception as e:
            logger.warning(f"Error fetching tasks for date {date_str}: {e}")
            day_tasks = []

        if not day_tasks:
            day_tasks_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.EVENT_AVAILABLE_ROUNDED, size=40, color=COLOR_SUCCESS),
                            ft.Text(
                                "На этот день дедлайнов нет! 🎉",
                                size=13,
                                color=ft.Colors.GREY_400,
                                weight=ft.FontWeight.W_500,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                    ),
                    padding=30,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for t in day_tasks:
                priority = calculate_priority(t)
                is_done = t.status == TaskStatus.DONE
                status_text = "Выполнено" if is_done else ("В процессе" if t.status == TaskStatus.DOING else "Сделать")
                status_color = COLOR_SUCCESS if is_done else (COLOR_WARNING if t.status == TaskStatus.DOING else COLOR_PRIMARY)

                day_tasks_list.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text(
                                            t.subject,
                                            size=13,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.WHITE,
                                        ),
                                        ft.Container(
                                            content=ft.Text(status_text, size=10, weight=ft.FontWeight.BOLD, color=status_color),
                                            bgcolor=ft.Colors.with_opacity(0.15, status_color),
                                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                            border_radius=6,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Text(t.description, size=12, color=ft.Colors.GREY_300, max_lines=2),
                                ft.Row(
                                    [
                                        ft.Text(f"Сложность: {t.effort_score}", size=10, color=COLOR_WARNING, weight=ft.FontWeight.W_600),
                                        ft.Text(f"Приоритет: {priority:.2f}", size=10, color=COLOR_PRIMARY, weight=ft.FontWeight.W_600),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                            ],
                            spacing=4,
                        ),
                        padding=10,
                        border_radius=8,
                        border=ft.border.all(1, BG_CARD_BORDER),
                        bgcolor=BG_CARD,
                    )
                )
        page.open(dialog)

    def update_calendar_grid(tasks=None):
        year = calendar_state["year"]
        month = calendar_state["month"]

        month_names = {
            1: "Январь",
            2: "Февраль",
            3: "Март",
            4: "Апрель",
            5: "Май",
            6: "Июнь",
            7: "Июль",
            8: "Август",
            9: "Сентябрь",
            10: "Октябрь",
            11: "Ноябрь",
            12: "Декабрь",
        }
        month_label.value = f"{month_names[month]} {year}"

        weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        header_row = ft.Row(
            [
                ft.Container(
                    content=ft.Text(
                        day,
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_PRIMARY if day in ("Сб", "Вс") else ft.Colors.GREY_400,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    expand=True,
                    alignment=ft.alignment.center,
                )
                for day in weekdays
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        calendar_grid_col.controls = [header_row]

        cal = calendar.Calendar(firstweekday=0)
        month_days = list(cal.itermonthdays4(year, month))

        if tasks is None:
            try:
                start_date_str = f"{month_days[0][0]:04d}-{month_days[0][1]:02d}-{month_days[0][2]:02d}"
                end_date_str = f"{month_days[-1][0]:04d}-{month_days[-1][1]:02d}-{month_days[-1][2]:02d}"
                tasks = db.get_tasks_in_date_range(start_date_str, end_date_str)
            except Exception as e:
                logger.warning(f"Error fetching tasks in date range: {e}")
                tasks = []

        weeks_data = [month_days[i : i + 7] for i in range(0, len(month_days), 7)]
        today_str = date.today().isoformat()

        from collections import defaultdict

        tasks_by_date = defaultdict(list)
        for t in tasks:
            tasks_by_date[get_clean_date(t.deadline)].append(t)

        def day_hover(e):
            is_hov = e.data == "true"
            e.control.scale = 1.025 if is_hov else 1.0
            e.control.shadow = (
                ft.BoxShadow(
                    blur_radius=8,
                    color=ft.Colors.with_opacity(0.18, COLOR_PRIMARY),
                    offset=ft.Offset(0, 2),
                )
                if is_hov
                else None
            )
            e.control.update()

        for week in weeks_data:
            week_row = ft.Row(spacing=4, alignment=ft.MainAxisAlignment.CENTER)
            for y, m, d, wd in week:
                day_date_str = f"{y:04d}-{m:02d}-{d:02d}"
                is_current_month = m == month
                is_today = day_date_str == today_str

                if is_today:
                    bgcolor = BG_TODAY
                    border_color = COLOR_PRIMARY
                elif is_current_month:
                    bgcolor = BG_CARD
                    border_color = BG_CARD_BORDER
                else:
                    bgcolor = ft.Colors.with_opacity(0.02, ft.Colors.WHITE)
                    border_color = ft.Colors.with_opacity(0.05, ft.Colors.WHITE)

                day_color = ft.Colors.WHITE if is_current_month else ft.Colors.GREY_600
                if is_today:
                    day_color = COLOR_PRIMARY

                day_tasks = tasks_by_date[day_date_str]

                task_capsules = []
                for t in day_tasks[:2]:
                    if t.status == TaskStatus.DONE:
                        cap_bg = ft.Colors.with_opacity(0.15, COLOR_SUCCESS)
                        cap_color = COLOR_SUCCESS
                        text_decor = ft.TextDecoration.LINE_THROUGH
                    else:
                        priority = calculate_priority(t)
                        if priority >= 2.5:
                            cap_bg = ft.Colors.with_opacity(0.2, COLOR_DANGER)
                            cap_color = COLOR_DANGER
                            text_decor = None
                        elif priority >= 1.5:
                            cap_bg = ft.Colors.with_opacity(0.2, COLOR_WARNING)
                            cap_color = COLOR_WARNING
                            text_decor = None
                        else:
                            cap_bg = ft.Colors.with_opacity(0.15, COLOR_PRIMARY)
                            cap_color = COLOR_PRIMARY
                            text_decor = None

                    task_capsules.append(
                        ft.Container(
                            content=ft.Text(
                                t.subject,
                                size=9,
                                weight=ft.FontWeight.W_600,
                                color=cap_color,
                                style=ft.TextStyle(decoration=text_decor),
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            bgcolor=cap_bg,
                            border_radius=4,
                            padding=ft.padding.symmetric(horizontal=4, vertical=1),
                            alignment=ft.alignment.center_left,
                        )
                    )

                if len(day_tasks) > 2:
                    task_capsules.append(
                        ft.Text(
                            f"+{len(day_tasks) - 2} еще",
                            size=8,
                            color=COLOR_PRIMARY,
                            weight=ft.FontWeight.BOLD,
                        )
                    )

                day_box = ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        str(d),
                                        size=11,
                                        weight=ft.FontWeight.BOLD if is_today or is_current_month else ft.FontWeight.NORMAL,
                                        color=day_color,
                                    ),
                                    *(
                                        [
                                            ft.Container(
                                                width=5,
                                                height=5,
                                                border_radius=3,
                                                bgcolor=COLOR_PRIMARY,
                                            )
                                        ]
                                        if is_today
                                        else []
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Column(
                                task_capsules,
                                spacing=2,
                                alignment=ft.MainAxisAlignment.START,
                                horizontal_alignment=ft.CrossAxisAlignment.START,
                            ),
                        ],
                        spacing=3,
                        alignment=ft.MainAxisAlignment.START,
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                    ),
                    expand=True,
                    height=78,
                    border=ft.border.all(1.5 if is_today else 1, border_color),
                    border_radius=8,
                    bgcolor=bgcolor,
                    padding=5,
                    scale=1.0,
                    animate_scale=100,
                    on_hover=day_hover,
                    on_click=lambda e, y=y, m=m, d=d: open_day_dialog(y, m, d),
                )
                week_row.controls.append(day_box)
            calendar_grid_col.controls.append(week_row)
        page.update()

    def change_month(delta):
        m = calendar_state["month"] + delta
        y = calendar_state["year"]
        if m < 1:
            m = 12
            y -= 1
        elif m > 12:
            m = 1
            y += 1
        calendar_state["month"] = m
        calendar_state["year"] = y
        update_calendar_grid()

    prev_month_btn = ft.IconButton(
        icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
        icon_size=14,
        tooltip="Предыдущий месяц",
        on_click=lambda _: change_month(-1),
    )
    next_month_btn = ft.IconButton(
        icon=ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
        icon_size=14,
        tooltip="Следующий месяц",
        on_click=lambda _: change_month(1),
    )

    calendar_view = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Icon(
                                    ft.Icons.CALENDAR_MONTH_ROUNDED,
                                    color=COLOR_PRIMARY,
                                    size=20,
                                ),
                                ft.Text(
                                    "Календарная сетка дедлайнов",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Container(
                            content=ft.Row([prev_month_btn, month_label, next_month_btn], spacing=4),
                            bgcolor=BG_CARD,
                            border=ft.border.all(1, BG_CARD_BORDER),
                            border_radius=10,
                            padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                calendar_grid_col,
            ],
            spacing=10,
            expand=True,
        ),
        padding=ft.padding.all(4),
        expand=True,
    )

    return calendar_view, update_calendar_grid
