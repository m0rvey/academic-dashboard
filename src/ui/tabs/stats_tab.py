from datetime import date

import flet as ft

from src.core.logger import setup_logger
from src.ui.constants import BG_CARD

logger = setup_logger("stats_tab")


def create_stats_tab():
    """Создаёт и возвращает содержимое вкладки «Статистика» и ссылки на обновляемые элементы."""
    kpi_row = ft.Row(spacing=10)

    # Выпадающий список выбора периода
    period_dropdown = ft.Dropdown(
        label="Период",
        value="all",
        options=[
            ft.dropdown.Option("all", "Всё время"),
            ft.dropdown.Option("today", "Сегодня"),
            ft.dropdown.Option("week", "Неделя"),
            ft.dropdown.Option("month", "Месяц"),
        ],
        width=150,
        text_size=13,
        border_radius=8,
        border_color=ft.Colors.GREY_700,
    )

    stats_chart = ft.PieChart(sections=[], sections_space=2, center_space_radius=35, expand=True)
    legend_wrap = ft.Row(wrap=True, spacing=10, run_spacing=5, alignment=ft.MainAxisAlignment.CENTER)

    tag_load_list = ft.ListView(expand=True, spacing=10)

    productivity_chart = ft.BarChart(
        bar_groups=[],
        border=ft.border.all(1, ft.Colors.GREY_800),
        left_axis=ft.ChartAxis(
            labels_size=30,
            show_labels=True,
        ),
        bottom_axis=ft.ChartAxis(
            labels=[],
            labels_size=20,
            show_labels=True,
        ),
        horizontal_grid_lines=ft.ChartGridLines(color=ft.Colors.GREY_800, width=1, dash_pattern=[3, 3]),
        expand=True,
    )

    stats_view = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(
                            "Общая статистика успеваемости",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.LIGHT_BLUE_200,
                        ),
                        period_dropdown,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                kpi_row,
                ft.Container(height=5),
                ft.Row(
                    [
                        # Левая панель - Дисциплины (PieChart + Legend)
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Icon(
                                                ft.Icons.PIE_CHART_OUTLINE_ROUNDED,
                                                color=ft.Colors.LIGHT_BLUE_200,
                                                size=20,
                                            ),
                                            ft.Text(
                                                "Нагрузка по дисциплинам",
                                                size=15,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.WHITE,
                                            ),
                                        ],
                                        spacing=6,
                                    ),
                                    ft.Divider(color=ft.Colors.GREY_800, height=1),
                                    ft.Container(
                                        content=stats_chart,
                                        height=180,
                                        alignment=ft.alignment.center,
                                        padding=ft.padding.all(5),
                                    ),
                                    ft.Container(
                                        content=legend_wrap,
                                        alignment=ft.alignment.center,
                                        padding=ft.padding.symmetric(vertical=5),
                                    ),
                                    ft.Text(
                                        "*(сумма сложности невыполненных задач)",
                                        size=11,
                                        color=ft.Colors.GREY_500,
                                        italic=True,
                                    ),
                                ],
                                spacing=10,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            bgcolor=BG_CARD,
                            border=ft.border.all(1, ft.Colors.GREY_800),
                            border_radius=12,
                            padding=16,
                            expand=True,
                        ),
                        # Средняя панель - Продуктивность (BarChart)
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Icon(
                                                ft.Icons.BAR_CHART_ROUNDED,
                                                color=ft.Colors.LIGHT_BLUE_200,
                                                size=20,
                                            ),
                                            ft.Text(
                                                "Продуктивность (7 дней)",
                                                size=15,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.WHITE,
                                            ),
                                        ],
                                        spacing=6,
                                    ),
                                    ft.Divider(color=ft.Colors.GREY_800, height=1),
                                    ft.Container(
                                        content=productivity_chart,
                                        height=205,
                                        padding=ft.padding.all(5),
                                    ),
                                    ft.Text(
                                        "*(количество выполненных задач по дедлайнам)",
                                        size=11,
                                        color=ft.Colors.GREY_500,
                                        italic=True,
                                    ),
                                ],
                                spacing=10,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            bgcolor=BG_CARD,
                            border=ft.border.all(1, ft.Colors.GREY_800),
                            border_radius=12,
                            padding=16,
                            expand=True,
                        ),
                        # Правая панель - Теги
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Icon(
                                                ft.Icons.LOCAL_OFFER_OUTLINED,
                                                color=ft.Colors.LIGHT_BLUE_200,
                                                size=20,
                                            ),
                                            ft.Text(
                                                "Нагрузка по тегам",
                                                size=15,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.WHITE,
                                            ),
                                        ],
                                        spacing=6,
                                    ),
                                    ft.Divider(color=ft.Colors.GREY_800, height=1),
                                    ft.Container(
                                        content=tag_load_list,
                                        height=205,
                                        padding=ft.padding.symmetric(vertical=5),
                                    ),
                                    ft.Text(
                                        "*(сумма сложности по активным тегам)",
                                        size=11,
                                        color=ft.Colors.GREY_500,
                                        italic=True,
                                    ),
                                ],
                                spacing=10,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            bgcolor=BG_CARD,
                            border=ft.border.all(1, ft.Colors.GREY_800),
                            border_radius=12,
                            padding=16,
                            expand=True,
                        ),
                    ],
                    spacing=15,
                    expand=True,
                ),
            ],
            spacing=15,
            expand=True,
        ),
        padding=ft.padding.all(10),
        expand=True,
    )

    return (
        stats_view,
        kpi_row,
        stats_chart,
        tag_load_list,
        legend_wrap,
        productivity_chart,
        period_dropdown,
    )


def update_kpi_cards(db, kpi_row, period_dropdown) -> None:
    """Обновляет KPI-карточки данными из БД."""
    from src.ui.components.kpi_card import create_kpi_card

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

    completion_rate = f"{completed_tasks_count} / {total_tasks_count}" if total_tasks_count > 0 else "0 / 0"

    kpi_row.controls = [
        create_kpi_card(
            "Всего задач",
            str(total_tasks_count),
            ft.Icons.LIST_ALT_ROUNDED,
            ft.Colors.BLUE_400,
        ),
        create_kpi_card(
            "Выполнено",
            completion_rate,
            ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
            ft.Colors.GREEN_400,
        ),
        create_kpi_card(
            "Просрочено",
            str(overdue_count),
            ft.Icons.WARNING_AMBER_ROUNDED,
            ft.Colors.RED_400,
        ),
        create_kpi_card(
            "Срочные",
            str(high_priority_count),
            ft.Icons.SPEED_ROUNDED,
            ft.Colors.AMBER_400,
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
) -> None:
    """Обновляет графики статистики: PieChart, BarChart продуктивности и нагрузку по тегам."""
    period = period_dropdown.value
    try:
        subjects_load = db.get_subject_load(period)
    except Exception as e:
        logger.warning(f"Error getting subject load: {e}")
        subjects_load = {}

    # 1. Pie Chart + Legend
    sections = []
    legend_wrap.controls.clear()
    if not subjects_load:
        sections.append(ft.PieChartSection(1, title="Нет задач", color=ft.Colors.GREY_700, radius=40))
    else:
        for subj, val in subjects_load.items():
            subj_color = get_subject_color(subj)
            sections.append(
                ft.PieChartSection(
                    val,
                    title=f"{val} ед.",
                    color=subj_color,
                    radius=45,
                    title_style=ft.TextStyle(size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                )
            )
            # Добавляем в легенду
            legend_wrap.controls.append(
                ft.Row(
                    [
                        ft.Container(width=10, height=10, border_radius=5, bgcolor=subj_color),
                        ft.Text(f"{subj}: {val} ед.", size=11, color=ft.Colors.GREY_400),
                    ],
                    spacing=5,
                    tight=True,
                )
            )
    stats_chart.sections = sections

    # 2. Productivity Bar Chart (Last 7 Days completed tasks)
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
                            color=(ft.Colors.GREEN_400 if count > 0 else ft.Colors.GREY_800),
                            width=12,
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
                            color=ft.Colors.GREY_500,
                            weight=ft.FontWeight.W_500,
                        ),
                        margin=ft.margin.only(top=5),
                    ),
                )
            )

    productivity_chart.bar_groups = bar_groups
    productivity_chart.bottom_axis = ft.ChartAxis(labels=bottom_labels)
    productivity_chart.max_y = max(max_count + 1, 5)

    # 3. Tag Load List (Grouped by Exams, Study, Other)
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
                    "Нет активных тегов для отображения нагрузки",
                    size=13,
                    color=ft.Colors.GREY_500,
                    italic=True,
                ),
                alignment=ft.alignment.center,
                padding=20,
            )
        )
    else:
        max_load = max(tag_load.values()) if tag_load else 1

        # Группируем теги
        EXAM_TAG_NAMES = {"огэ", "егэ", "экзамен", "зачет", "тест", "контрольная"}
        STUDY_TAG_NAMES = {
            "дз",
            "лаба",
            "семинар",
            "лекция",
            "проект",
            "чтение",
            "конспект",
        }

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

        def render_tag_group(title: str, items: list, header_color: str):
            if not items:
                return
            tag_load_list.controls.append(
                ft.Container(
                    content=ft.Text(title, size=12, weight=ft.FontWeight.BOLD, color=header_color),
                    padding=ft.padding.only(top=5, bottom=2),
                )
            )
            for tag, score in sorted(items, key=lambda x: x[1], reverse=True):
                tag_load_list.controls.append(
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Text(
                                    tag,
                                    size=11,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                                bgcolor=(
                                    ft.Colors.RED_900
                                    if header_color == ft.Colors.RED_300
                                    else (
                                        ft.Colors.GREEN_900
                                        if header_color == ft.Colors.GREEN_300
                                        else ft.Colors.BLUE_GREY_900
                                    )
                                ),
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=10,
                                width=110,
                            ),
                            ft.ProgressBar(
                                value=score / max_load,
                                color=ft.Colors.LIGHT_BLUE_400,
                                bgcolor=ft.Colors.GREY_800,
                                expand=True,
                                height=6,
                            ),
                            ft.Text(
                                f"{score} ед.",
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREY_400,
                            ),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                )

        # Рендерим группы в порядке приоритета
        render_tag_group("🔥 Экзамены & Контрольные", exams, ft.Colors.RED_300)
        render_tag_group("📚 Учебный процесс", study, ft.Colors.GREEN_300)
        render_tag_group("⚙️ Другое", other, ft.Colors.BLUE_GREY_300)
