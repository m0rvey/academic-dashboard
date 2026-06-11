import flet as ft

from src.core.grade_calculator import calculate_needed_grades
from src.ui.constants import BG_CARD


def create_grades_tab(page: ft.Page, db):
    """Создаёт и возвращает содержимое вкладки «Успеваемость», диалог калькулятора и ссылки на обновляемые элементы."""

    # Grades View Setup
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
                ft.Icon(ft.Icons.SCHOOL_ROUNDED, size=64, color=ft.Colors.GREY_600),
                ft.Text(
                    "Нет данных по успеваемости",
                    size=18,
                    color=ft.Colors.WHITE,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Отмечайте задачи как выполненные и выставляйте им оценки в списке задач,\nчтобы увидеть статистику среднего балла по предметам.",
                    size=13,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=50,
        alignment=ft.alignment.center,
        visible=True,
    )

    grades_layout_container = ft.Column(
        [
            grades_kpi_row,
            ft.Container(height=5),
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
                                            color=ft.Colors.LIGHT_BLUE_200,
                                            size=20,
                                        ),
                                        ft.Text(
                                            "Успеваемость по предметам",
                                            size=15,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.WHITE,
                                        ),
                                    ],
                                    spacing=6,
                                ),
                                ft.Divider(color=ft.Colors.GREY_800, height=1),
                                ft.Container(
                                    content=subject_grades_list,
                                    height=230,
                                    padding=ft.padding.symmetric(vertical=5),
                                ),
                                ft.Text(
                                    "*(средний балл по выполненным задачам)",
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
                    # Right panel
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
                                            "График успеваемости",
                                            size=15,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.WHITE,
                                        ),
                                    ],
                                    spacing=6,
                                ),
                                ft.Divider(color=ft.Colors.GREY_800, height=1),
                                ft.Container(
                                    content=grades_chart,
                                    height=230,
                                    padding=ft.padding.all(10),
                                ),
                                ft.Text(
                                    "*(визуализация среднего балла по предметам)",
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
        expand=True,
        spacing=15,
        visible=False,
    )

    # Target Calculator Dialog Setup
    calc_subject = ft.Dropdown(label="Выберите предмет", width=280, border_color=ft.Colors.GREY_800)
    calc_target = ft.Slider(min=2.0, max=5.0, divisions=30, value=4.5, label="{value}", width=280)
    calc_target_grade = ft.Dropdown(
        label="Планируемая оценка",
        value="5",
        options=[
            ft.dropdown.Option("5", "5 (Отлично)"),
            ft.dropdown.Option("4", "4 (Хорошо)"),
        ],
        width=280,
        border_color=ft.Colors.GREY_800,
    )
    calc_result_text = ft.Text(
        "Выберите предмет и целевой балл для расчета.",
        size=13,
        color=ft.Colors.GREY_400,
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
                f"🟢 Вы уже достигли цели! Текущий балл по предмету '{subj}': {current_avg:.2f}\n"
                f"Целевой балл: {target_gpa:.2f}"
            )
        else:
            calc_result_text.value = (
                f"🎯 Чтобы достичь балла {target_gpa:.2f} (сейчас {current_avg:.2f}),\n"
                f"вам нужно получить еще **{res}** шт. '{planned_g}' подряд!"
            )
        page.update()

    calc_subject.on_change = run_calculator_logic
    calc_target.on_change = run_calculator_logic
    calc_target_grade.on_change = run_calculator_logic

    calculator_dialog = ft.AlertDialog(
        title=ft.Text("🎯 Калькулятор целевого балла", weight=ft.FontWeight.BOLD),
        content=ft.Column(
            [
                calc_subject,
                ft.Row(
                    [ft.Text("Цель:", size=11, color=ft.Colors.GREY_400), calc_target],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                calc_target_grade,
                ft.Divider(color=ft.Colors.GREY_800),
                calc_result_text,
            ],
            tight=True,
            spacing=15,
            width=320,
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
                        ft.Text(
                            "Успеваемость и оценки",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.LIGHT_BLUE_200,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.ADJUST,
                            icon_color=ft.Colors.LIGHT_BLUE_200,
                            tooltip="Калькулятор целей",
                            on_click=open_calculator,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                grades_placeholder,
                grades_layout_container,
            ],
            spacing=15,
            expand=True,
        ),
        padding=ft.padding.all(10),
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
    from src.core.logger import setup_logger
    from src.ui.components.kpi_card import create_kpi_card

    logger = setup_logger("grades_tab")

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
                "Средний балл",
                f"{overall_gpa:.2f}",
                ft.Icons.SCHOOL_ROUNDED,
                ft.Colors.AMBER_400,
            ),
            create_kpi_card(
                "Всего оценок",
                str(total_grades_count),
                ft.Icons.GRADE_ROUNDED,
                ft.Colors.BLUE_400,
            ),
            create_kpi_card(
                "Отлично (5) / Хорошо (4)",
                f"{count_5} / {count_4}",
                ft.Icons.STAR_ROUNDED,
                ft.Colors.GREEN_400,
            ),
            create_kpi_card(
                "Удовл. (3) / Неудовл. (2)",
                f"{count_3} / {count_2}",
                ft.Icons.STAR_HALF_ROUNDED,
                ft.Colors.ORANGE_400,
            ),
        ]

        subject_grades_list.controls.clear()
        bar_groups = []
        bottom_labels = []
        for idx, (subj, data_dict) in enumerate(sorted(subj_gpas.items())):
            gpa = data_dict["gpa"]
            count = data_dict["count"]
            if gpa >= 4.5:
                bar_color = ft.Colors.GREEN_ACCENT_400
            elif gpa >= 3.5:
                bar_color = ft.Colors.AMBER_ACCENT_400
            else:
                bar_color = ft.Colors.RED_ACCENT_400

            subject_grades_list.controls.append(
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(
                                subj,
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                            ),
                            bgcolor=ft.Colors.BLUE_GREY_900,
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            border_radius=10,
                            width=120,
                        ),
                        ft.ProgressBar(
                            value=gpa / 5.0,
                            color=bar_color,
                            bgcolor=ft.Colors.GREY_800,
                            expand=True,
                            height=6,
                        ),
                        ft.Text(
                            f"{gpa:.2f} ({count} оц.)",
                            size=11,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_400,
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
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
                            width=16,
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
                            subj[:8] + ".." if len(subj) > 8 else subj,
                            size=9,
                            weight=ft.FontWeight.W_500,
                        ),
                        margin=ft.margin.only(top=5),
                    ),
                )
            )
        grades_chart.bar_groups = bar_groups
        grades_chart.bottom_axis = ft.ChartAxis(labels=bottom_labels)
