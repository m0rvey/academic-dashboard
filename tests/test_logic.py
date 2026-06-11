from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from src.core.grade_calculator import calculate_needed_grades
from src.core.logic import calculate_priority, get_daily_load
from src.core.models import Task, TaskStatus
from src.core.nlp_parser import parse_natural_language_task


def test_calculate_priority_normal():
    # Task due in 2 days, effort 3
    deadline = (date.today() + timedelta(days=2)).isoformat()
    task = Task(
        subject="Математика",
        description="Домашка",
        deadline=deadline,
        effort_score=3,
        tags=[],
    )
    # days_left = 2
    # priority = 3 / (2 + 1) = 1.0
    assert calculate_priority(task) == 1.0


def test_calculate_priority_special_tag():
    # Task with "ОГЭ" tag, due in 1 day, effort 4
    deadline = (date.today() + timedelta(days=1)).isoformat()
    task = Task(
        subject="Русский язык",
        description="Сочинение",
        deadline=deadline,
        effort_score=4,
        tags=["ОГЭ", "Подготовка"],
    )
    # days_left = 1
    # priority = 4 / (1 + 1) * 1.5 = 2.0 * 1.5 = 3.0
    assert calculate_priority(task) == 3.0


def test_calculate_priority_overdue():
    # Overdue task (days_left is negative)
    deadline = (date.today() - timedelta(days=5)).isoformat()
    task = Task(subject="Физика", description="Лаба", deadline=deadline, effort_score=2, tags=[])
    # days_left = max(0, -5) = 0
    # priority = 2 / (0 + 1) = 2.0
    assert calculate_priority(task) == 2.0


def test_get_daily_load():
    tasks = [
        Task(
            subject="A",
            description="D",
            deadline="2026-05-29",
            effort_score=3,
            status=TaskStatus.TODO,
        ),
        Task(
            subject="B",
            description="D",
            deadline="2026-05-29",
            effort_score=5,
            status=TaskStatus.DOING,
        ),
        Task(
            subject="C",
            description="D",
            deadline="2026-05-29",
            effort_score=2,
            status=TaskStatus.DONE,
        ),
    ]
    # Sum of effort_score for non-DONE tasks: 3 + 5 = 8
    assert get_daily_load(tasks) == 8


def test_parse_natural_language_task():
    # 1. Standard pattern
    res1 = parse_natural_language_task("Запиши домашку по физике лаба 3 на завтра сложность 4")
    assert res1 is not None
    assert res1["subject"] == "Физика"
    assert res1["description"] == "Лаба 3"
    assert res1["effort_score"] == 4
    assert res1["deadline"] == (date.today() + timedelta(days=1)).isoformat()

    # 2. Today deadline, standard mapping
    res2 = parse_natural_language_task("математика контрольная на сегодня сложность 7")
    assert res2["subject"] == "Математика"
    assert res2["description"] == "Контрольная"
    assert res2["effort_score"] == 7
    assert res2["deadline"] == date.today().isoformat()

    # 3. Weekday deadline and fallback default difficulty (1)
    res3 = parse_natural_language_task("Добавь лабу по химии на понедельник")
    assert res3["subject"] == "Химия"
    assert res3["description"] == "Лабу"
    assert res3["effort_score"] == 1  # Default fallback
    # Calculate expected Monday date
    today = date.today()
    days_ahead = 0 - today.weekday()  # Monday is 0
    if days_ahead <= 0:
        days_ahead += 7
    expected_deadline = (today + timedelta(days_ahead)).isoformat()
    assert res3["deadline"] == expected_deadline

    # 4. Unknown subject mapping falls back to capitalizing first word
    res4 = parse_natural_language_task("программирование сделать проект на послезавтра сложность 9")
    assert res4["subject"] == "Программирование"
    assert res4["description"] == "Сделать проект"
    assert res4["effort_score"] == 9
    assert res4["deadline"] == (date.today() + timedelta(days=2)).isoformat()


def test_calculate_needed_grades():
    # Current grades: 4, 4. Target: 4.5. Planned grade: 5.
    # Current sum: 8, n=2.
    # (8 + 5k) / (2 + k) >= 4.5
    # 8 + 5k >= 9 + 4.5k => 0.5k >= 1 => k >= 2.
    k = calculate_needed_grades([4, 4], 4.5, 5)
    assert k == 2

    # Already achieved target
    k_achieved = calculate_needed_grades([5, 5], 4.5, 5)
    assert k_achieved == 0

    # Impossible target
    k_impossible = calculate_needed_grades([3, 3], 4.5, 4)
    assert k_impossible is None


def test_parse_empty_string():
    """Пустая строка должна вернуть None."""
    assert parse_natural_language_task("") is None
    assert parse_natural_language_task("   ") is None


def test_parse_only_whitespace():
    """Строка из пробелов должна вернуть None."""
    assert parse_natural_language_task("     ") is None


def test_parse_explicit_date():
    """Явная дата в формате YYYY-MM-DD должна корректно парситься."""
    res = parse_natural_language_task("домашка по алгебре 2026-06-15 сложность 3")
    assert res is not None
    assert res["subject"] == "Математика"  # алгебра -> Математика
    assert res["deadline"] == "2026-06-15"
    assert res["effort_score"] == 3


def test_parse_poslezvtra():
    """'послезавтра' должно парситься в today + 2."""
    res = parse_natural_language_task("физика лабораторная на послезавтра")
    assert res is not None
    assert res["subject"] == "Физика"
    assert res["deadline"] == (date.today() + timedelta(days=2)).isoformat()


def test_parse_no_subject_match():
    """Неизвестный предмет должен капитализироваться."""
    res = parse_natural_language_task("Кулинария сделать торт на завтра")
    assert res is not None
    assert res["subject"] == "Кулинария"


def test_parse_default_effort():
    """Если сложность не указана, должна быть 1."""
    res = parse_natural_language_task("запиши домашку по русскому")
    assert res is not None
    assert res["effort_score"] == 1


def test_parse_effort_out_of_range():
    """Сложность > 10 должна игнорироваться, оставляя дефолт 1."""
    res = parse_natural_language_task("математика задание 15 на сегодня")
    assert res is not None
    # 15 не в диапазоне 1-10, значит effort должен быть 1
    assert res["effort_score"] == 1


def test_parse_nlp_exam_tags():
    """Проверяет распознавание тегов ОГЭ, ЕГЭ и различных словоформ слова 'экзамен'."""
    # 1. Точное совпадение "экзамен"
    res1 = parse_natural_language_task("экзамен по математике на завтра")
    assert "Экзамен" in res1["tags"]

    # 2. Склоняемая форма "экзамену"
    res2 = parse_natural_language_task("подготовка к экзамену по физике")
    assert "Экзамен" in res2["tags"]

    # 3. Множественное число "экзамены"
    res3 = parse_natural_language_task("сдать экзамены на следующей неделе")
    assert "Экзамен" in res3["tags"]

    # 4. Аббревиатура "ОГЭ" (точный поиск)
    res4 = parse_natural_language_task("подготовка к огэ")
    assert "ОГЭ" in res4["tags"]

    # 5. Аббревиатура "ЕГЭ" (точный поиск)
    res5 = parse_natural_language_task("сдать егэ по информатике")
    assert "ЕГЭ" in res5["tags"]


def test_parse_nlp_mangled_numbers():
    """Проверяет, что при удалении сложности не ломаются другие числа, совпадающие с ней."""
    res = parse_natural_language_task("история 4 класс 4")
    assert res["subject"] == "История"
    assert res["description"] == "4 класс"
    assert res["effort_score"] == 4


def test_parse_nlp_dates_not_parsed_as_effort():
    """Проверяет, что числа внутри дедлайна YYYY-MM-DD не извлекаются как сложность."""
    res = parse_natural_language_task("математика домашнее задание на 2026-06-05")
    assert res["subject"] == "Математика"
    assert res["deadline"] == "2026-06-05"
    assert res["effort_score"] == 1  # Ожидаемый дефолт, т.к. 06 и 05 из даты проигнорированы


def test_parse_slang_subjects():
    """Проверяет корректное распознавание сленговых названий предметов."""
    test_cases = [
        ("домашка по матану", "Математика"),
        ("инфа завтра сложность 5", "Информатика"),
        ("физра принести форму", "Физкультура"),
        ("подготовка к общаге", "Обществознание"),
        ("англ перевод", "Английский язык"),
    ]
    for text, expected_subject in test_cases:
        res = parse_natural_language_task(text)
        assert res is not None
        assert res["subject"] == expected_subject


def test_parse_nlp_advanced_dates():
    # Через N дней
    res1 = parse_natural_language_task("сдать матан через 3 дня сложность 5")
    assert res1["deadline"] == (date.today() + timedelta(days=3)).isoformat()

    # Через неделю
    res2 = parse_natural_language_task("проект по инфе через неделю")
    assert res2["deadline"] == (date.today() + timedelta(days=7)).isoformat()

    # В следующую среду
    res3 = parse_natural_language_task("сдать проект в следующую среду")
    today = date.today()
    days_ahead = 2 - today.weekday()  # 2 is Wednesday
    if days_ahead <= 0:
        days_ahead += 7
    days_ahead += 7  # "следующую"
    assert res3["deadline"] == (today + timedelta(days=days_ahead)).isoformat()


def test_parse_nlp_custom_tags():
    # Хэштеги #tag
    res1 = parse_natural_language_task("надо подготовить доклад по истории #олимпиада #важно")
    assert "Олимпиада" in res1["tags"]
    assert "Важно" in res1["tags"]
    assert "олимпиада" not in res1["description"].lower()

    # Явные слова тег/хэштег
    res2 = parse_natural_language_task("математика тег проект хэштег срочно")
    assert "Проект" in res2["tags"]
    assert "Срочно" in res2["tags"]


def test_parse_new_subjects():
    test_cases = [
        ("нарисовать чертеж по черчению", "Черчение"),
        ("сделать проект по однкнр", "ОДНКНР"),
        ("изо нарисовать плакат", "ИЗО"),
        ("труд сделать табуретку", "Технология"),
        ("прога написать код", "Программирование"),
        ("астрономия выучить звезды", "Астрономия"),
    ]
    for text, expected_subject in test_cases:
        res = parse_natural_language_task(text)
        assert res is not None
        assert res["subject"] == expected_subject


def test_task_pydantic_validation():
    # 1. Invalid subject raises ValidationError
    with pytest.raises(ValidationError):
        Task(subject="", description="desc", deadline="2026-06-01", effort_score=5)

    # 2. Invalid description raises ValidationError
    with pytest.raises(ValidationError):
        Task(subject="Math", description="  ", deadline="2026-06-01", effort_score=5)

    # 3. Invalid effort_score raises ValidationError
    with pytest.raises(ValidationError):
        Task(subject="Math", description="desc", deadline="2026-06-01", effort_score=11)

    # 4. Invalid grade raises ValidationError
    with pytest.raises(ValidationError):
        Task(
            subject="Math",
            description="desc",
            deadline="2026-06-01",
            effort_score=5,
            grade=6,
        )

    # 5. Invalid assignment raises ValidationError due to validate_assignment=True
    t = Task(subject="Math", description="desc", deadline="2026-06-01", effort_score=5)
    with pytest.raises(ValidationError):
        t.effort_score = 0
