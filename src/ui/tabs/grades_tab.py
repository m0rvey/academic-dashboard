import flet as ft

from src.core.grade_calculator import calculate_needed_grades
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

logger = setup_logger("grades_tab")


def create_grades_tab(page: ft.Page, db):
    """Создаёт и возвращает содержимое вкладки «Успеваемость», диалог калькулятора и ссылки на обновляемые элементы."""

    grades_kpi_row = ft.Row(spacing=10)

    grades_chart = ft.BarChart(
        bar_groups=[],
        min_y=0,
        max_y=5,
        left_axis=ft.ChartAxis(
            labels=[
                ft.ChartAxisLabel(value=0, label=ft.Text("0", size=10, color=ft.Colors.GREY_500)),
                ft.ChartAxisLabel(value=1, label=ft.Text("1", size=10, color=ft.Colors.GREY_500)),
                ft.ChartAxisLabel(value=2, label=ft.Text("2", size=10, color=ft.Colors.GREY_500)),
                ft.ChartAxisLabel(value=3, label=ft.Text("3", size=10, color=ft.Colors.GREY_500)),
                ft.ChartAxisLabel(value=4, label=ft.Text("4", size=10, color=ft.Colors.GREY_500)),
                ft.ChartAxisLabel(value=5, label=ft.Text("5", size=10, color=ft.Colors.GREY_500)),
            ]
        ),
        bottom_axis=ft.ChartAxis(labels=[]),
        expand=True,
    )

    subject_grades_list = ft.ListView(expand=True, spacing=10)

    grades_placeholder = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.SCHOOL_ROUNDED, size=56, color=ft.Colors.GREY_600),
                ft.Text(
                    "Нет данных об успеваемости",
                    size=16,
                    color=ft.Colors.WHITE,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Выставляйте оценки за выполненные задачи, чтобы отслеживать GPA и динамику успеваемости.",
                    size=13,
                    color=ft.Colors.GREY_400,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        padding=60,
        alignment=ft.alignment.center,
        visible=True,
    )

    grades_layout_container = ft.Column(
        [
            grades_kpi_row,
            ft.Container(height=4),
            ft.Row(
                [
                    # Left panel
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(
                                            ft.Icons.FACT_CHECK_ROUNDED,
                                            color=COLOR_PRIMARY,
                                            size=18,
                                        ),
                                        ft.Text(
                                            "Средний балл по предметам",
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.WHITE,
                                        ),
                                    ],
                                    spacing=8,
                                ),
                                ft.Divider(color=BG_CARD_BORDER, height=1),
                                ft.Container(
                                    content=subject_grades_list,
                                    height=240,
                                    padding=ft.padding.symmetric(vertical=4),
                                ),
                            ],
                            spacing=10,
                        ),
                        bgcolor=BG_CARD,
                        border=ft.border.all(1, BG_CARD_BORDER),
                        border_radius=12,
                        padding=16,
                        expand=True,
                    ),
                    # Right panel
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(
                                            ft.Icons.BAR_CHART_ROUNDED,
                                            color=COLOR_PRIMARY,
                                            size=18,
                                        ),
                                        ft.Text(
                                            "График среднего балла",
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.WHITE,
                                        ),
                                    ],
                                    spacing=8,
                                ),
                                ft.Divider(color=BG_CARD_BORDER, height=1),
                                ft.Container(
                                    content=grades_chart,
                                    height=240,
                                    padding=ft.padding.all(8),
                                ),
                            ],
                            spacing=10,
                        ),
                        bgcolor=BG_CARD,
                        border=ft.border.all(1, BG_CARD_BORDER),
                        border_radius=12,
                        padding=16,
                        expand=True,
                    ),
                ],
                spacing=12,
                expand=True,
            ),
        ],
        expand=True,
        spacing=12,
        visible=False,
    )

    # Target Calculator Dialog Setup
    calc_subject = ft.Dropdown(
        label="Выберите предмет",
        width=300,
        border_color=BG_CARD_BORDER,
        focused_border_color=COLOR_PRIMARY,
        border_radius=8,
    )
    calc_target = ft.Slider(
        min=2.0,
        max=5.0,
        divisions=30,
        value=4.75,
        label="{value}",
        width=300,
        active_color=COLOR_PRIMARY,
    )
    calc_target_grade = ft.Dropdown(
        label="Планируемая оценка",
        value="5",
        options=[
            ft.dropdown.Option("5", "5 (Отлично)"),
            ft.dropdown.Option("4", "4 (Хорошо)"),
        ],
        width=300,
        border_color=BG_CARD_BORDER,
        focused_border_color=COLOR_PRIMARY,
        border_radius=8,
    )
    calc_result_text = ft.Text(
        "Выберите предмет и целевой балл для расчета.",
        size=13,
        color=ft.Colors.GREY_300,
        weight=ft.FontWeight.W_500,
    )

    def run_calculator_logic(e):
        subj = calc_subject.value
        if not subj:
            calc_result_text.value = "Пожалуйста, выберите предмет."
            page.update()
            return

        graded_tasks = db.get_tasks_with_grades()
        subject_graded_tasks = [t for t in graded_tasks if t.subject == subj]
        subject_grades = [t.grade for t in subject_graded_tasks]

        if not subject_grades:
            calc_result_text.value = "По этому предмету еще нет полученных оценок."
            page.update()
            return

        target_gpa = float(calc_target.value)
        planned_g = int(calc_target_grade.value)

        res = calculate_needed_grades(subject_grades, target_gpa, planned_g)
        current_avg = sum(subject_grades) / len(subject_grades)

        if res is None:
            calc_result_text.value = (
                f"❌ Невозможно достичь балла {target_gpa:.2f}, получая только {planned_g}-ки.\n"
                f"Текущий средний балл по предмету '{subj}': {current_avg:.2f}"
            )
        elif res == 0:
            calc_result_text.value = (
                f"🟢 Цель уже достигнута! Текущий балл по предмету '{subj}': {current_avg:.2f}\n"
                f"Целевой балл: {target_gpa:.2f}"
            )
        else:
            calc_result_text.value = (
                f"🎯 Чтобы повысить средний балл с {current_avg:.2f} до {target_gpa:.2f},\n"
                f"вам нужно получить ещё **{res}** шт. '{planned_g}' подряд!"
            )
        page.update()

    calc_subject.on_change = run_calculator_logic
    calc_target.on_change = run_calculator_logic
    calc_target_grade.on_change = run_calculator_logic

    calculator_dialog = ft.AlertDialog(
        title=ft.Row(
            [
                ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color=COLOR_PRIMARY, size=20),
                ft.Text("Калькулятор целевого балла", weight=ft.FontWeight.BOLD, size=16),
            ],
            spacing=8,
        ),
        content=ft.Container(
            content=ft.Column(
                [
                    calc_subject,
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text("Целевой GPA:", size=12, color=ft.Colors.GREY_400, weight=ft.FontWeight.W_600),
                                    ft.Text(f"{calc_target.value:.2f}", size=12, color=COLOR_PRIMARY, weight=ft.FontWeight.BOLD),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            calc_target,
                        ],
                        spacing=4,
                    ),
                    calc_target_grade,
                    ft.Container(
                        content=calc_result_text,
                        bgcolor=ft.Colors.with_opacity(0.08, COLOR_PRIMARY),
                        padding=12,
                        border_radius=8,
                        border=ft.border.all(1, ft.Colors.with_opacity(0.2, COLOR_PRIMARY)),
                    ),
                ],
                tight=True,
                spacing=12,
                width=340,
            ),
        ),
        actions=[ft.TextButton("Закрыть", on_click=lambda e: page.close(calculator_dialog))],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_calculator(e):
        completed_graded = db.get_tasks_with_grades()
        subjects_with_grades = sorted(list(set(t.subject for t in completed_graded)))

        calc_subject.options = [ft.dropdown.Option(s) for s in subjects_with_grades]
        if subjects_with_grades:
            calc_subject.value = subjects_with_grades[0]
        else:
            calc_subject.value = None

        calc_result_text.value = "Выберите предмет и целевой балл для расчета."
        run_calculator_logic(None)
        page.open(calculator_dialog)

    grades_view = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.SCHOOL_ROUNDED, color=COLOR_PRIMARY, size=20),
                                ft.Text(
                                    "Академическая успеваемость и GPA",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.FilledButton(
                            "Калькулятор целей",
                            icon=ft.Icons.AUTO_AWESOME_ROUNDED,
                            on_click=open_calculator,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                grades_placeholder,
                grades_layout_container,
            ],
            spacing=12,
            expand=True,
        ),
        padding=ft.padding.all(4),
    )

    return (
        grades_view,
        grades_placeholder,
        grades_layout_container,
        grades_kpi_row,
        subject_grades_list,
        grades_chart,
    )


def update_grades_view(
    db,
    grades_placeholder,
    grades_layout_container,
    grades_kpi_row,
    subject_grades_list,
    grades_chart,
) -> None:
    """Обновляет вкладку успеваемости: KPI оценок, список предметов с GPA и bar-chart."""
    try:
        grades_info = db.get_grades_stats()
        subj_gpas = db.get_subject_grades_gpa()
    except Exception as e:
        logger.warning(f"Error getting grades stats: {e}")
        grades_info = {}
        subj_gpas = {}

    if not grades_info:
        grades_placeholder.visible = True
        grades_layout_container.visible = False
    else:
        grades_placeholder.visible = False
        grades_layout_container.visible = True

        overall_gpa = grades_info["gpa"]
        total_grades_count = grades_info["total_count"]
        count_5 = grades_info["count_5"]
        count_4 = grades_info["count_4"]
        count_3 = grades_info["count_3"]
        count_2 = grades_info["count_2"]

        grades_kpi_row.controls = [
            create_kpi_card(
                "Общий средний балл (GPA)",
                f"{overall_gpa:.2f}",
                ft.Icons.AUTO_AWESOME_ROUNDED,
                COLOR_PRIMARY,
            ),
            create_kpi_card(
                "Всего оценок",
                str(total_grades_count),
                ft.Icons.NUMBERS_ROUNDED,
                COLOR_PRIMARY,
            ),
            create_kpi_card(
                "Отлично (5) / Хорошо (4)",
                f"{count_5} / {count_4}",
                ft.Icons.STAR_ROUNDED,
                COLOR_SUCCESS,
            ),
            create_kpi_card(
                "Удовл. (3) / Неудовл. (2)",
                f"{count_3} / {count_2}",
                ft.Icons.WARNING_AMBER_ROUNDED,
                COLOR_WARNING if count_3 > 0 or count_2 > 0 else ft.Colors.GREY_500,
            ),
        ]

        subject_grades_list.controls.clear()
        bar_groups = []
        bottom_labels = []
        for idx, (subj, data_dict) in enumerate(sorted(subj_gpas.items())):
            gpa = data_dict["gpa"]
            count = data_dict["count"]
            if gpa >= 4.5:
                bar_color = COLOR_SUCCESS
            elif gpa >= 3.5:
                bar_color = COLOR_WARNING
            else:
                bar_color = COLOR_DANGER

            subject_grades_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                subj,
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                                width=110,
                                no_wrap=True,
                            ),
                            ft.ProgressBar(
                                value=gpa / 5.0,
                                color=bar_color,
                                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                                expand=True,
                                height=6,
                                border_radius=4,
                            ),
                            ft.Text(
                                f"{gpa:.2f} ({count} оц.)",
                                size=11,
                                weight=ft.FontWeight.W_600,
                                color=bar_color,
                                width=80,
                                text_align=ft.TextAlign.RIGHT,
                            ),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.padding.symmetric(vertical=4),
                )
            )

            bar_groups.append(
                ft.BarChartGroup(
                    x=idx,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0,
                            to_y=gpa,
                            color=bar_color,
                            width=18,
                            border_radius=4,
                            tooltip=f"{subj}: {gpa:.2f}",
                        )
                    ],
                )
            )
            bottom_labels.append(
                ft.ChartAxisLabel(
                    value=idx,
                    label=ft.Container(
                        content=ft.Text(
                            subj[:6] + ".." if len(subj) > 6 else subj,
                            size=9,
                            weight=ft.FontWeight.W_500,
                            color=ft.Colors.GREY_400,
                        ),
                        margin=ft.margin.only(top=6),
                    ),
                )
            )
        grades_chart.bar_groups = bar_groups
        grades_chart.bottom_axis = ft.ChartAxis(labels=bottom_labels)
