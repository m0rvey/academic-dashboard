import calendar
from datetime import date, datetime

import flet as ft

from src.core.logger import setup_logger
from src.core.logic import calculate_priority
from src.core.models import TaskStatus, get_clean_date
from src.ui.constants import BG_CARD, BG_DARK, BG_TODAY

logger = setup_logger("calendar_tab")


def create_calendar_tab(db, page: ft.Page):
    """Создаёт и возвращает содержимое вкладки «Календарь» и функцию обновления сетки."""
    calendar_state = {"year": datetime.today().year, "month": datetime.today().month}

    month_label = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.LIGHT_BLUE_200)
    calendar_grid_col = ft.Column(spacing=5, expand=True)

    def open_day_dialog(y, m, d):
        date_str = f"{y:04d}-{m:02d}-{d:02d}"
        day_tasks_list = ft.ListView(expand=True, spacing=10, height=200)

        dialog_ref = [None]
        dialog = ft.AlertDialog(
            title=ft.Text(f"Дедлайн на {d:02d}.{m:02d}.{y}", weight=ft.FontWeight.BOLD),
            content=ft.Column([day_tasks_list], tight=True, width=350),
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
                ft.Text(
                    "В этот день дедлайнов нет! Отдыхайте 🎉",
                    size=13,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER,
                )
            )
        else:
            for t in day_tasks:
                priority = calculate_priority(t)
                is_done = t.status == TaskStatus.DONE
                status_text = "Выполнено" if is_done else ("В процессе" if t.status == TaskStatus.DOING else "TODO")
                status_color = (
                    ft.Colors.GREEN_400
                    if is_done
                    else (ft.Colors.AMBER_400 if t.status == TaskStatus.DOING else ft.Colors.BLUE_400)
                )

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
                                        ft.Text(
                                            status_text,
                                            size=10,
                                            weight=ft.FontWeight.BOLD,
                                            color=status_color,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Text(t.description, size=12, color=ft.Colors.GREY_400),
                                ft.Row(
                                    [
                                        ft.Text(
                                            f"Сложность: {t.effort_score}",
                                            size=10,
                                            color=ft.Colors.GREY_500,
                                        ),
                                        ft.Text(
                                            f"Приоритет: {priority:.2f}",
                                            size=10,
                                            color=ft.Colors.GREY_500,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                            ],
                            spacing=4,
                        ),
                        padding=8,
                        border_radius=8,
                        border=ft.border.all(1, ft.Colors.GREY_800),
                        bgcolor=BG_DARK,
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
                        color=ft.Colors.GREY_400,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    width=95,
                    alignment=ft.alignment.center,
                )
                for day in weekdays
            ],
            spacing=5,
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
            if e.data == "true":
                e.control.scale = 1.03
                e.control.shadow = ft.BoxShadow(
                    blur_radius=8,
                    color=ft.Colors.with_opacity(0.3, ft.Colors.LIGHT_BLUE_400),
                    offset=ft.Offset(0, 2),
                )
            else:
                e.control.scale = 1.0
                e.control.shadow = None
            e.control.update()

        for week in weeks_data:
            week_row = ft.Row(spacing=5, alignment=ft.MainAxisAlignment.CENTER)
            for y, m, d, wd in week:
                day_date_str = f"{y:04d}-{m:02d}-{d:02d}"
                is_current_month = m == month
                is_today = day_date_str == today_str

                if is_today:
                    bgcolor = BG_TODAY
                    border_color = ft.Colors.LIGHT_BLUE_400
                elif is_current_month:
                    bgcolor = BG_CARD
                    border_color = ft.Colors.GREY_800
                else:
                    bgcolor = BG_DARK
                    border_color = ft.Colors.GREY_900

                day_color = ft.Colors.WHITE if is_current_month else ft.Colors.GREY_600
                if is_today:
                    day_color = ft.Colors.LIGHT_BLUE_200

                day_tasks = tasks_by_date[day_date_str]

                task_capsules = []
                for t in day_tasks[:3]:
                    if t.status == TaskStatus.DONE:
                        cap_color = ft.Colors.GREY_800
                        text_decor = ft.TextDecoration.LINE_THROUGH
                        text_color = ft.Colors.GREY_500
                    else:
                        priority = calculate_priority(t)
                        if priority >= 2.5:
                            cap_color = ft.Colors.RED_900
                            text_decor = None
                            text_color = ft.Colors.WHITE
                        elif priority >= 1.5:
                            cap_color = ft.Colors.AMBER_900
                            text_decor = None
                            text_color = ft.Colors.WHITE
                        else:
                            cap_color = ft.Colors.TEAL_900
                            text_decor = None
                            text_color = ft.Colors.WHITE

                    task_capsules.append(
                        ft.Container(
                            content=ft.Text(
                                t.subject,
                                size=9,
                                weight=ft.FontWeight.W_500,
                                color=text_color,
                                style=ft.TextStyle(decoration=text_decor),
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            bgcolor=cap_color,
                            border_radius=4,
                            padding=ft.padding.symmetric(horizontal=4, vertical=1),
                            alignment=ft.alignment.center_left,
                            width=90,
                        )
                    )

                if len(day_tasks) > 3:
                    task_capsules.append(
                        ft.Text(
                            f"+ еще {len(day_tasks) - 3}",
                            size=9,
                            color=ft.Colors.GREY_500,
                            italic=True,
                            weight=ft.FontWeight.W_500,
                        )
                    )

                day_box = ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                str(d),
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=day_color,
                            ),
                            ft.Column(
                                task_capsules,
                                spacing=2,
                                alignment=ft.MainAxisAlignment.START,
                                horizontal_alignment=ft.CrossAxisAlignment.START,
                            ),
                        ],
                        spacing=4,
                        alignment=ft.MainAxisAlignment.START,
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                    ),
                    width=95,
                    height=85,
                    border=ft.border.all(1, border_color),
                    border_radius=8,
                    bgcolor=bgcolor,
                    padding=6,
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
        icon_size=16,
        on_click=lambda _: change_month(-1),
    )
    next_month_btn = ft.IconButton(
        icon=ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
        icon_size=16,
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
                                    color=ft.Colors.LIGHT_BLUE_200,
                                    size=20,
                                ),
                                ft.Text(
                                    "Календарь дедлайнов",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                            ],
                            spacing=6,
                        ),
                        ft.Row([prev_month_btn, month_label, next_month_btn], spacing=10),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(color=ft.Colors.GREY_800, height=1),
                calendar_grid_col,
            ],
            spacing=15,
            expand=True,
        ),
        padding=ft.padding.all(10),
        expand=True,
    )

    return calendar_view, update_calendar_grid
