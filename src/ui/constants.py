"""Константы пользовательского интерфейса Academic Dashboard."""

import flet as ft

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

# Цвета диаграмм
CHART_COLORS = [
    ft.Colors.BLUE_500,
    ft.Colors.RED_500,
    ft.Colors.GREEN_500,
    ft.Colors.AMBER_500,
    ft.Colors.PURPLE_500,
    ft.Colors.CYAN_500,
    ft.Colors.PINK_500,
    ft.Colors.TEAL_500,
]

# Цвета фона (тёмная тема)
BG_CARD = (
    ft.Colors.SURFACE_CONTAINER_LOW
    if hasattr(ft.Colors, "SURFACE_CONTAINER_LOW")
    else ft.Colors.SURFACE_VARIANT
    if hasattr(ft.Colors, "SURFACE_VARIANT")
    else ft.Colors.GREY_900
)
BG_CARD_HOVER = (
    ft.Colors.SURFACE_CONTAINER_HIGH
    if hasattr(ft.Colors, "SURFACE_CONTAINER_HIGH")
    else ft.Colors.SURFACE_VARIANT
    if hasattr(ft.Colors, "SURFACE_VARIANT")
    else ft.Colors.GREY_800
)
BG_DARK = ft.Colors.BACKGROUND if hasattr(ft.Colors, "BACKGROUND") else ft.Colors.BLACK
BG_TODAY = ft.Colors.BLUE_900
