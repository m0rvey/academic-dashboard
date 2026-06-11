from src.bot.state import BotState
from src.core.models import Task, TaskStatus


def test_bot_state_caches_active_tasks(db):
    state = BotState(db)
    task = Task(subject="Мат", description="Дз", deadline="2099-01-01", effort_score=5)
    db.add_task(task)

    tasks1 = state.get_active_tasks()
    tasks2 = state.get_active_tasks()
    assert tasks1 is tasks2
    assert len(tasks1) == 1


def test_bot_state_invalidates_cache(db):
    state = BotState(db)
    task = Task(subject="Мат", description="Дз", deadline="2099-01-01", effort_score=5)
    db.add_task(task)

    tasks1 = state.get_active_tasks()
    assert len(tasks1) == 1

    state.invalidate()
    task2 = Task(subject="Физ", description="Лаба", deadline="2099-01-02", effort_score=3)
    db.add_task(task2)

    tasks2 = state.get_active_tasks()
    assert len(tasks2) == 2
    assert tasks1 is not tasks2


def test_bot_state_caches_kpi_stats(db):
    state = BotState(db)
    task = Task(subject="Мат", description="Дз", deadline="2099-01-01", effort_score=5)
    db.add_task(task)

    stats1 = state.get_kpi_stats("all")
    stats2 = state.get_kpi_stats("all")
    assert stats1 is stats2
    assert stats1["total"] == 1


def test_bot_state_kpi_different_periods_independent(db):
    state = BotState(db)
    stats_week = state.get_kpi_stats("week")
    stats_month = state.get_kpi_stats("month")
    assert stats_week is not stats_month


def test_bot_state_caches_grades(db):
    state = BotState(db)
    task = Task(subject="Мат", description="Дз", deadline="2099-01-01", effort_score=5, status=TaskStatus.DONE, grade=5)
    db.add_task(task, notify=False)

    grades1 = state.get_grades_stats()
    grades2 = state.get_grades_stats()
    assert grades1 is grades2
    assert grades1["gpa"] == 5.0


def test_bot_state_sorted_active_tasks(db):
    state = BotState(db)
    from datetime import date, timedelta

    t1 = Task(subject="А", description="Д", deadline=date.today().isoformat(), effort_score=3)
    t2 = Task(subject="Б", description="Д", deadline=(date.today() + timedelta(days=1)).isoformat(), effort_score=8)
    db.add_task(t1, notify=False)
    db.add_task(t2, notify=False)

    sorted_tasks = state.get_sorted_active_tasks()
    assert len(sorted_tasks) == 2
    # t2 has higher effort and closer deadline — should be first
    assert sorted_tasks[0].subject == "Б"


def test_bot_state_invalidate_clears_grades(db):
    state = BotState(db)
    task = Task(subject="Мат", description="Дз", deadline="2099-01-01", effort_score=5, status=TaskStatus.DONE, grade=4)
    db.add_task(task, notify=False)

    grades1 = state.get_grades_stats()
    state.invalidate()
    grades2 = state.get_grades_stats()
    assert grades1 is not grades2
