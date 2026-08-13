from unittest.mock import MagicMock, patch

import flet as ft

from src.ui.views import run_gui


# Extract main function from run_gui locally without launching app
def get_main_func(db):
    main_func = None

    def fake_app(target, *args, **kwargs):
        nonlocal main_func
        main_func = target

    with patch.object(ft, "app", side_effect=fake_app):
        run_gui(db)

    return main_func


def test_smoke_ui(db):
    def fake_getenv(key, default=None):
        if key == "TELEGRAM_BOT_TOKEN":
            return "123456789:ABCdef"
        if key == "TELEGRAM_ALLOWED_USERS":
            return "123456789"
        return default

    with patch("os.getenv", side_effect=fake_getenv):
        main_func = get_main_func(db)
        assert main_func is not None, "main function not found"

        page = MagicMock(spec=ft.Page)
        page.overlay = []
        page.session = MagicMock()
        page.client_storage = MagicMock()
        page.client_storage.get.return_value = None

        def fake_open(dialog):
            if dialog not in page.overlay:
                page.overlay.append(dialog)

        page.open = MagicMock(side_effect=fake_open)

        def fake_close(dialog):
            if dialog in page.overlay:
                page.overlay.remove(dialog)

        # Run the main UI startup
        main_func(page)

        # Verify that the UI added elements
        assert page.add.called

        # Click Floating Action Button to open Add dialog
        assert page.floating_action_button is not None
        page.floating_action_button.on_click(None)

        assert len(page.overlay) > 0

        # Creating a task through the mocked UI callbacks
        # The add_dialog should be in page.overlay
        dialog = next((x for x in page.overlay if isinstance(x, ft.AlertDialog)), None)
        assert dialog is not None, "Add dialog not found"


def test_smoke_ui_without_env(db, tmp_path):
    temp_env = tmp_path / ".env"

    with patch("src.core.config.ENV_PATH", temp_env), \
         patch("os.getenv", return_value=""):

        main_func = get_main_func(db)
        # When .env is missing or unconfigured, run_gui returns early and ft.app (main_func) is never called
        assert main_func is None




def test_smoke_tasks_tab():
    from src.ui.tabs.tasks_tab import create_tasks_tab

    session_config = {
        "current_tab": "tasks",
        "search_query": "",
        "filter_status": "Все",
        "filter_tag": "Все",
        "sort_by": "По приоритету",
    }
    tasks_view, search_field, filter_status, filter_tag, sort_dropdown, task_list = create_tasks_tab(
        session_config, lambda: None, lambda: None
    )
    assert isinstance(tasks_view, ft.Column)
    assert isinstance(search_field, ft.TextField)
    assert isinstance(filter_status, ft.Dropdown)
    assert isinstance(filter_tag, ft.Dropdown)
    assert isinstance(sort_dropdown, ft.Dropdown)
    assert isinstance(task_list, ft.ListView)


def test_smoke_stats_tab():
    from src.ui.tabs.stats_tab import create_stats_tab

    (
        stats_view,
        kpi_row,
        stats_chart,
        tag_load_list,
        legend_wrap,
        productivity_chart,
        period_dropdown,
    ) = create_stats_tab()
    assert isinstance(stats_view, ft.Container)
    assert isinstance(kpi_row, ft.Row)
    assert isinstance(stats_chart, ft.PieChart)
    assert isinstance(tag_load_list, ft.ListView)
    assert isinstance(productivity_chart, ft.BarChart)
    assert isinstance(period_dropdown, ft.Dropdown)


def test_smoke_grades_tab():
    from src.ui.tabs.grades_tab import create_grades_tab

    db = MagicMock()
    page = MagicMock(spec=ft.Page)
    (
        grades_view,
        grades_placeholder,
        grades_layout_container,
        grades_kpi_row,
        subject_grades_list,
        grades_chart,
    ) = create_grades_tab(page, db)
    assert isinstance(grades_view, ft.Container)
    assert isinstance(grades_placeholder, ft.Container)
    assert isinstance(grades_kpi_row, ft.Row)
    assert isinstance(subject_grades_list, ft.ListView)
    assert isinstance(grades_chart, ft.BarChart)


def test_smoke_calendar_tab():
    from src.ui.tabs.calendar_tab import create_calendar_tab

    db = MagicMock()
    page = MagicMock(spec=ft.Page)
    calendar_view, update_calendar_grid = create_calendar_tab(db, page)
    assert isinstance(calendar_view, ft.Container)
    assert callable(update_calendar_grid)
