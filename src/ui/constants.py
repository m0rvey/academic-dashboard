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
    ft.colors.BLUE_500,
    ft.colors.RED_500,
    ft.colors.GREEN_500,
    ft.colors.AMBER_500,
    ft.colors.PURPLE_500,
    ft.colors.CYAN_500,
    ft.colors.PINK_500,
    ft.colors.TEAL_500,
]

# Цвета фона (тёмная тема)
BG_CARD = (
    ft.colors.SURFACE_CONTAINER_LOW
    if hasattr(ft.colors, "SURFACE_CONTAINER_LOW")
    else ft.colors.SURFACE_VARIANT
    if hasattr(ft.colors, "SURFACE_VARIANT")
    else ft.colors.GREY_900
)
BG_CARD_HOVER = (
    ft.colors.SURFACE_CONTAINER_HIGH
    if hasattr(ft.colors, "SURFACE_CONTAINER_HIGH")
    else ft.colors.SURFACE_VARIANT
    if hasattr(ft.colors, "SURFACE_VARIANT")
    else ft.colors.GREY_800
)
BG_DARK = ft.colors.BACKGROUND if hasattr(ft.colors, "BACKGROUND") else ft.colors.BLACK
BG_TODAY = ft.colors.BLUE_900
