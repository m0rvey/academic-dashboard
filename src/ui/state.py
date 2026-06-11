from typing import Dict, List

from src.core.models import Task


class AppState:
    """Кэшированное состояние приложения для ускорения рендеринга."""

    def __init__(self, db):
        self.db = db
        self.all_tasks: List[Task] = []
        self.tags: List[str] = []

        # Индексы вкладок: 0: Tasks, 1: Stats, 2: Grades, 3: Calendar
        self.dirty_tabs: Dict[int, bool] = {0: True, 1: True, 2: True, 3: True}

        # Кэш цветов предметов
        import flet as ft

        # Предзаполняем базовыми цветами
        self.subject_colors: Dict[str, str] = {
            "Математика": ft.Colors.BLUE_500,
            "Физика": ft.Colors.RED_500,
            "Химия": ft.Colors.GREEN_500,
            "Информатика": ft.Colors.AMBER_500,
            "История": ft.Colors.PURPLE_500,
            "Литература": ft.Colors.CYAN_500,
            "Биология": ft.Colors.PINK_500,
            "География": ft.Colors.TEAL_500,
        }

    def get_subject_color(self, subj: str) -> str:
        from src.ui.constants import CHART_COLORS

        if subj not in self.subject_colors:
            color_idx = len(self.subject_colors) % len(CHART_COLORS)
            self.subject_colors[subj] = CHART_COLORS[color_idx]
        return self.subject_colors[subj]

    def reload(self):
        """Полностью перезагружает кэш из БД и помечает все вкладки грязными."""
        try:
            self.all_tasks = self.db.get_all_tasks()
            self.tags = self.db.get_all_tags()
        except Exception as e:
            from src.core.logger import setup_logger

            logger = setup_logger("state")
            logger.error(f"Error reloading state: {e}")
            self.all_tasks = []
            self.tags = []
        self.mark_all_dirty()

    def mark_all_dirty(self):
        """Помечает все вкладки как требующие обновления."""
        for k in self.dirty_tabs:
            self.dirty_tabs[k] = True

    def mark_clean(self, tab_index: int):
        """Помечает вкладку как актуальную."""
        self.dirty_tabs[tab_index] = False

    def is_dirty(self, tab_index: int) -> bool:
        """Проверяет, нужно ли обновлять вкладку."""
        return self.dirty_tabs.get(tab_index, True)
