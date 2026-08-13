from datetime import date

import flet as ft

from src.core.logger import setup_logger
from src.ui.components.kpi_card import create_kpi_card
from src.ui.constants import (
    BG_CARD,
    BG_CARD_BORDER,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_WARNING,
)

logger = setup_logger("stats_tab")


def create_stats_tab():
    """Создаёт и возвращает содержимое вкладки «Статистика» с современным Donut-чартом и аналитикой."""
    kpi_row = ft.Row(spacing=10)

    period_dropdown = ft.Dropdown(
        label="Период",
        value="all",
        options=[
            ft.dropdown.Option("all", "Всё время"),
            ft.dropdown.Option("today", "Сегодня"),
            ft.dropdown.Option("week", "Последние 7 дней"),
            ft.dropdown.Option("month", "Этот месяц"),
        ],
        width=170,
        text_size=12,
        border_radius=10,
        border_color=BG_CARD_BORDER,
        focused_border_color=COLOR_PRIMARY,
        dense=True,
    )

    # Красивый Donut Chart со сводкой в центре
    total_load_label = ft.Text("0", size=22, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY)
    total_load_sub = ft.Text("ед. нагрузки", size=10, color=ft.Colors.GREY_400, weight=ft.FontWeight.W_500)

    donut_center_widget = ft.Container(
        content=ft.Column(
            [
                total_load_label,
                total_load_sub,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        ),
        alignment=ft.alignment.center,
    )

    stats_chart = ft.PieChart(
        sections=[],
        sections_space=3,
        center_space_radius=52,
        expand=True,
    )

    chart_stack = ft.Stack(
        [
            stats_chart,
            donut_center_widget,
        ],
        width=200,
        height=180,
        alignment=ft.alignment.center,
    )

    legend_wrap = ft.Row(wrap=True, spacing=6, run_spacing=4, alignment=ft.MainAxisAlignment.CENTER)
    tag_load_list = ft.ListView(expand=True, spacing=6)

    productivity_chart = ft.BarChart(
        bar_groups=[],
        border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
        left_axis=ft.ChartAxis(
            labels_size=24,
            show_labels=True,
        ),
        bottom_axis=ft.ChartAxis(
            labels=[],
            labels_size=20,
            show_labels=True,
        ),
        horizontal_grid_lines=ft.ChartGridLines(color=ft.Colors.with_opacity(0.08, ft.Colors.WHITE), width=1, dash_pattern=[3, 3]),
        expand=True,
    )

    stats_view = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.ANALYTICS_ROUNDED, color=COLOR_PRIMARY, size=20),
                                ft.Text(
                                    "Аналитика и распределение нагрузки",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                            ],
                            spacing=8,
                        ),
                        period_dropdown,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                kpi_row,
                ft.Container(height=4),
                ft.Row(
                    [
                        # Левая панель - Дисциплины (Donut + Center Info + Legend)
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Icon(
                                                ft.Icons.DONUT_LARGE_ROUNDED,
                                                color=COLOR_PRIMARY,
                                                size=18,
                                            ),
                                            ft.Text(
                                                "По дисциплинам",
                                                size=14,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.WHITE,
                                            ),
                                        ],
                                        spacing=6,
                                    ),
                                    ft.Divider(color=BG_CARD_BORDER, height=1),
                                    ft.Container(
                                        content=chart_stack,
                                        height=180,
                                        alignment=ft.alignment.center,
                                        padding=ft.padding.all(2),
                                    ),
                                    ft.Container(
                                        content=legend_wrap,
                                        alignment=ft.alignment.center,
                                        padding=ft.padding.symmetric(vertical=2),
                                    ),
                                ],
                                spacing=6,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            bgcolor=BG_CARD,
                            border=ft.border.all(1, BG_CARD_BORDER),
                            border_radius=12,
                            padding=14,
                            expand=True,
                        ),
                        # Средняя панель - Продуктивность (BarChart)
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Icon(
                                                ft.Icons.SPEED_ROUNDED,
                                                color=COLOR_SUCCESS,
                                                size=18,
                                            ),
                                            ft.Text(
                                                "Выполнено за 7 дней",
                                                size=14,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.WHITE,
                                            ),
                                        ],
                                        spacing=6,
                                    ),
                                    ft.Divider(color=BG_CARD_BORDER, height=1),
                                    ft.Container(
                                        content=productivity_chart,
                                        height=215,
                                        padding=ft.padding.all(6),
                                    ),
                                ],
                                spacing=8,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            bgcolor=BG_CARD,
                            border=ft.border.all(1, BG_CARD_BORDER),
                            border_radius=12,
                            padding=14,
                            expand=True,
                        ),
                        # Правая панель - Теги
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Icon(
                                                ft.Icons.TAG_ROUNDED,
                                                color=COLOR_WARNING,
                                                size=18,
                                            ),
                                            ft.Text(
                                                "Нагрузка по тегам",
                                                size=14,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.WHITE,
                                            ),
                                        ],
                                        spacing=6,
                                    ),
                                    ft.Divider(color=BG_CARD_BORDER, height=1),
                                    ft.Container(
                                        content=tag_load_list,
                                        height=215,
                                        padding=ft.padding.symmetric(vertical=4),
                                    ),
                                ],
                                spacing=8,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            bgcolor=BG_CARD,
                            border=ft.border.all(1, BG_CARD_BORDER),
                            border_radius=12,
                            padding=14,
                            expand=True,
                        ),
                    ],
                    spacing=12,
                    expand=True,
                ),
            ],
            spacing=12,
            expand=True,
        ),
        padding=ft.padding.all(4),
        expand=True,
    )

    stats_view.total_load_label = total_load_label

    return (
        stats_view,
        kpi_row,
        stats_chart,
        tag_load_list,
        legend_wrap,
        productivity_chart,
        period_dropdown,
    )


def update_kpi_cards(db, kpi_row, period_dropdown, is_dark: bool = True) -> None:
    """Обновляет KPI-карточки данными из БД."""
    period = period_dropdown.value
    try:
        kpis = db.get_kpi_stats(period)
    except Exception as e:
        logger.warning(f"Error getting KPI stats: {e}")
        kpis = {"total": 0, "completed": 0, "overdue": 0, "high_priority": 0}

    total_tasks_count = kpis["total"]
    completed_tasks_count = kpis["completed"]
    overdue_count = kpis["overdue"]
    high_priority_count = kpis["high_priority"]

    completion_rate = f"{completed_tasks_count} / {total_tasks_count}" if total_tasks_count > 0 else "0"

    kpi_row.controls = [
        create_kpi_card(
            "Всего задач",
            str(total_tasks_count),
            ft.Icons.FORMAT_LIST_BULLETED_ROUNDED,
            COLOR_PRIMARY,
            subtitle=f"Период: {period_dropdown.options[0].text if period == 'all' else period}",
            is_dark=is_dark,
        ),
        create_kpi_card(
            "Выполнено",
            completion_rate,
            ft.Icons.CHECK_CIRCLE_ROUNDED,
            COLOR_SUCCESS,
            subtitle="Завершенные задачи",
            is_dark=is_dark,
        ),
        create_kpi_card(
            "Просрочено",
            str(overdue_count),
            ft.Icons.WARNING_AMBER_ROUNDED,
            COLOR_DANGER if overdue_count > 0 else ft.Colors.GREY_500,
            subtitle="Требуют внимания",
            is_dark=is_dark,
        ),
        create_kpi_card(
            "Срочные / Экзамены",
            str(high_priority_count),
            ft.Icons.LOCAL_FIRE_DEPARTMENT_ROUNDED,
            COLOR_WARNING if high_priority_count > 0 else ft.Colors.GREY_500,
            subtitle="Высокий приоритет",
            is_dark=is_dark,
        ),
    ]


def update_stats_charts(
    db,
    stats_chart,
    legend_wrap,
    productivity_chart,
    tag_load_list,
    period_dropdown,
    get_subject_color,
    stats_view: ft.Container = None,
) -> None:
    """Обновляет графики статистики: Donut Chart, BarChart продуктивности и нагрузку по тегам."""
    period = period_dropdown.value
    try:
        subjects_load = db.get_subject_load(period)
    except Exception as e:
        logger.warning(f"Error getting subject load: {e}")
        subjects_load = {}

    total_units = sum(subjects_load.values()) if subjects_load else 0
    if stats_view and hasattr(stats_view, "total_load_label"):
        stats_view.total_load_label.value = str(total_units)

    # 1. Donut Chart + Legend
    sections = []
    legend_wrap.controls.clear()
    if not subjects_load or total_units == 0:
        sections.append(
            ft.PieChartSection(
                1,
                title="",
                color=ft.Colors.with_opacity(0.15, ft.Colors.GREY_700),
                radius=26,
            )
        )
    else:
        for subj, val in subjects_load.items():
            subj_color = get_subject_color(subj)
            percent = int((val / total_units) * 100) if total_units > 0 else 0
            sections.append(
                ft.PieChartSection(
                    val,
                    title=f"{percent}%" if percent >= 8 else "",
                    color=subj_color,
                    radius=28,
                    title_style=ft.TextStyle(size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                )
            )
            legend_wrap.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(width=8, height=8, border_radius=4, bgcolor=subj_color),
                            ft.Text(f"{subj}: {val} ед. ({percent}%)", size=10, color=ft.Colors.GREY_300, weight=ft.FontWeight.W_500),
                        ],
                        spacing=4,
                        tight=True,
                    ),
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                    border_radius=6,
                )
            )
    stats_chart.sections = sections

    # 2. Productivity Bar Chart
    try:
        prod_data = db.get_completed_tasks_by_day_last_7_days()
    except Exception as e:
        logger.warning(f"Error getting completed tasks by day: {e}")
        prod_data = {}

    bar_groups = []
    bottom_labels = []
    max_count = 1
    if prod_data:
        max_count = max(max(prod_data.values()), 1)
        for idx, (date_str, count) in enumerate(sorted(prod_data.items())):
            try:
                dt = date.fromisoformat(date_str)
                label_text = dt.strftime("%d.%m")
            except ValueError:
                label_text = date_str[-5:]

            bar_groups.append(
                ft.BarChartGroup(
                    x=idx,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0,
                            to_y=count,
                            color=COLOR_SUCCESS if count > 0 else ft.Colors.with_opacity(0.2, ft.Colors.GREY_700),
                            width=16,
                            border_radius=4,
                            tooltip=f"{date_str}: {count} задач",
                        )
                    ],
                )
            )
            bottom_labels.append(
                ft.ChartAxisLabel(
                    value=idx,
                    label=ft.Container(
                        content=ft.Text(
                            label_text,
                            size=9,
                            color=ft.Colors.GREY_400,
                            weight=ft.FontWeight.W_500,
                        ),
                        margin=ft.margin.only(top=6),
                    ),
                )
            )

    productivity_chart.bar_groups = bar_groups
    productivity_chart.bottom_axis = ft.ChartAxis(labels=bottom_labels)
    productivity_chart.max_y = max(max_count + 1, 5)

    # 3. Tag Load List
    try:
        tag_load = db.get_tag_load(period)
    except Exception as e:
        logger.warning(f"Error getting tag load: {e}")
        tag_load = {}

    tag_load_list.controls.clear()
    if not tag_load:
        tag_load_list.controls.append(
            ft.Container(
                content=ft.Text(
                    "Нет активных тегов для отображения",
                    size=12,
                    color=ft.Colors.GREY_500,
                ),
                alignment=ft.alignment.center,
                padding=20,
            )
        )
    else:
        max_load = max(tag_load.values()) if tag_load else 1

        EXAM_TAG_NAMES = {"огэ", "егэ", "экзамен", "зачет", "тест", "контрольная"}
        STUDY_TAG_NAMES = {"дз", "лаба", "семинар", "лекция", "проект", "чтение", "конспект"}

        exams = []
        study = []
        other = []

        for tag, score in tag_load.items():
            tag_lower = tag.lower()
            if tag_lower in EXAM_TAG_NAMES:
                exams.append((tag, score))
            elif tag_lower in STUDY_TAG_NAMES:
                study.append((tag, score))
            else:
                other.append((tag, score))

        def render_tag_group(title: str, items: list, header_color: str, bar_c: str):
            if not items:
                return
            tag_load_list.controls.append(
                ft.Container(
                    content=ft.Text(title, size=11, weight=ft.FontWeight.BOLD, color=header_color),
                    padding=ft.padding.only(top=4, bottom=2),
                )
            )
            for tag, score in sorted(items, key=lambda x: x[1], reverse=True):
                tag_load_list.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text(
                                    f"#{tag}",
                                    size=11,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                    width=90,
                                    no_wrap=True,
                                ),
                                ft.ProgressBar(
                                    value=score / max_load,
                                    color=bar_c,
                                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                                    expand=True,
                                    height=5,
                                    border_radius=3,
                                ),
                                ft.Text(
                                    f"{score} ед.",
                                    size=10,
                                    weight=ft.FontWeight.W_600,
                                    color=ft.Colors.GREY_400,
                                    width=45,
                                    text_align=ft.TextAlign.RIGHT,
                                ),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.symmetric(vertical=2),
                    )
                )

        render_tag_group("🔥 Экзамены", exams, COLOR_DANGER, COLOR_DANGER)
        render_tag_group("📚 Учеба", study, COLOR_SUCCESS, COLOR_SUCCESS)
        render_tag_group("🏷️ Прочее", other, COLOR_PRIMARY, COLOR_PRIMARY)
