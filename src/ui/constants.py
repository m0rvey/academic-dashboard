"""Константы пользовательского интерфейса Academic Dashboard в стиле macOS Cupertino."""

# Фильтры задач
FILTER_ALL = "Все"
FILTER_ALL_TAGS = "Все теги"

# Статусы задач
STATUS_TODO = "TODO"
STATUS_DOING = "DOING"
STATUS_DONE = "DONE"

# Сортировки
SORT_DEADLINE = "Дедлайн (ближние)"
SORT_EFFORT = "Сложность (убыв.)"
SORT_SUBJECT = "Предмет (А-Я)"
SORT_PRIORITY = "Приоритет"

# Быстрые фильтры-чипы
CHIP_ALL = "Все задачи"
CHIP_URGENT = "🔥 Срочные"
CHIP_TODAY = "📅 На сегодня"
CHIP_OVERDUE = "🚨 Просрочено"
CHIP_EXAMS = "🎓 Экзамены"
CHIP_DONE = "✅ Выполненные"

# Цвета диаграмм (яркая современная палитра)
CHART_COLORS = [
    "#38BDF8",  # Sky Blue
    "#F43F5E",  # Rose
    "#10B981",  # Emerald
    "#F59E0B",  # Amber
    "#818CF8",  # Indigo
    "#06B6D4",  # Cyan
    "#EC4899",  # Pink
    "#14B8A6",  # Teal
    "#A855F7",  # Purple
]

# Дизайн-токены палитры macOS
COLOR_PRIMARY = "#38BDF8"       # Electric Sky Blue
COLOR_PRIMARY_DARK = "#0284C7"
COLOR_ACCENT_PURPLE = "#818CF8"  # Soft Indigo
COLOR_SUCCESS = "#10B981"       # Emerald
COLOR_WARNING = "#F59E0B"       # Amber
COLOR_DANGER = "#F43F5E"        # Crimson Rose
COLOR_MUTED = "#64748B"         # Slate Muted

# Фоны для тёмной темы
BG_DARK = "#0B0F19"             # Deep Space Obsidian
BG_SIDEBAR = "#0F172A"          # Slate Sidebar
BG_CARD = "#161F30"             # Frosted Card Base
BG_CARD_HOVER = "#1E293B"       # Elevated Card Hover
BG_CARD_BORDER = "#334155"      # Subtle Slate Border
BG_CARD_BORDER_GLOW = "#38BDF8" # Focus Border
BG_TODAY = "#1E3A8A"            # Deep Blue Highlight

# Фоны для светлой темы
BG_LIGHT = "#F8FAFC"
BG_LIGHT_SIDEBAR = "#F1F5F9"
BG_LIGHT_CARD = "#FFFFFF"
BG_LIGHT_CARD_HOVER = "#F1F5F9"
BG_LIGHT_BORDER = "#E2E8F0"
BG_LIGHT_TODAY = "#DBEAFE"


def get_theme_palette(is_dark: bool) -> dict:
    """Возвращает актуальную палитру цветов в зависимости от выбранной темы."""
    if is_dark:
        return {
            "bg_app": BG_DARK,
            "bg_sidebar": BG_SIDEBAR,
            "bg_card": BG_CARD,
            "bg_card_hover": BG_CARD_HOVER,
            "bg_card_border": BG_CARD_BORDER,
            "bg_today": BG_TODAY,
            "text_primary": "#FFFFFF",
            "text_secondary": "#94A3B8",
            "text_muted": "#64748B",
            "divider": BG_CARD_BORDER,
        }
    else:
        return {
            "bg_app": BG_LIGHT,
            "bg_sidebar": BG_LIGHT_SIDEBAR,
            "bg_card": BG_LIGHT_CARD,
            "bg_card_hover": BG_LIGHT_CARD_HOVER,
            "bg_card_border": BG_LIGHT_BORDER,
            "bg_today": BG_LIGHT_TODAY,
            "text_primary": "#0F172A",
            "text_secondary": "#475569",
            "text_muted": "#94A3B8",
            "divider": BG_LIGHT_BORDER,
        }
