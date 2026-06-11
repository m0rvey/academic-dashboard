import json
import os
import shutil
from unittest.mock import MagicMock

from src.core.database import DatabaseManager
from src.core.models import Task, TaskStatus


def test_init_db(db):
    # Database table should be created and we should get empty list of tasks
    tasks = db.get_all_tasks()
    assert len(tasks) == 0


def test_add_and_get_task(db):
    task = Task(
        subject="Информатика",
        description="Написать программу",
        deadline="2026-06-01",
        effort_score=4,
        tags=["Python", "ДЗ"],
        status=TaskStatus.TODO,
    )
    task_id = db.add_task(task)
    assert task_id is not None

    tasks = db.get_all_tasks()
    assert len(tasks) == 1
    db_task = tasks[0]
    assert db_task.id == task_id
    assert db_task.subject == "Информатика"
    assert db_task.description == "Написать программу"
    assert db_task.deadline == "2026-06-01"
    assert db_task.effort_score == 4
    assert db_task.tags == ["Python", "ДЗ"]
    assert db_task.status == TaskStatus.TODO


def test_update_task_status(db):
    task = Task(
        subject="Химия",
        description="Опыты",
        deadline="2026-05-30",
        effort_score=2,
        tags=[],
        status=TaskStatus.TODO,
    )
    task_id = db.add_task(task)

    # Update status to DOING
    success = db.update_task_status(task_id, TaskStatus.DOING)
    assert success is True

    tasks = db.get_all_tasks()
    assert tasks[0].status == TaskStatus.DOING


def test_update_task(db):
    task = Task(
        subject="История",
        description="Параграф 5",
        deadline="2026-05-28",
        effort_score=1,
        tags=["Чтение"],
        status=TaskStatus.TODO,
    )
    task_id = db.add_task(task)

    updated_task = Task(
        id=task_id,
        subject="История Нового Времени",
        description="Параграфы 5 и 6",
        deadline="2026-06-05",
        effort_score=3,
        tags=["Чтение", "Конспект"],
        status=TaskStatus.DOING,
    )
    success = db.update_task(updated_task)
    assert success is True

    tasks = db.get_all_tasks()
    assert len(tasks) == 1
    db_task = tasks[0]
    assert db_task.subject == "История Нового Времени"
    assert db_task.description == "Параграфы 5 и 6"
    assert db_task.deadline == "2026-06-05"
    assert db_task.effort_score == 3
    assert db_task.tags == ["Чтение", "Конспект"]
    assert db_task.status == TaskStatus.DOING


def test_delete_task(db):
    task = Task(
        subject="Биология",
        description="Доклад",
        deadline="2026-05-31",
        effort_score=2,
        tags=[],
        status=TaskStatus.TODO,
    )
    task_id = db.add_task(task)
    assert len(db.get_all_tasks()) == 1

    success = db.delete_task(task_id)
    assert success is True
    assert len(db.get_all_tasks()) == 0


def test_export_import_json(db, tmp_path):
    task1 = Task(
        subject="Math",
        description="Homework",
        deadline="2026-06-01",
        effort_score=3,
        tags=["Algebra"],
        status=TaskStatus.TODO,
    )
    task2 = Task(
        subject="English",
        description="Essay",
        deadline="2026-06-02",
        effort_score=5,
        tags=["Grammar", "Writing"],
        status=TaskStatus.DONE,
    )
    db.add_task(task1)
    db.add_task(task2)

    backup_path = tmp_path / "temp_backup.json"
    db.export_to_json(str(backup_path))
    assert backup_path.exists()

    # Create a new blank database
    db_path_2 = tmp_path / "temp_planner_2.db"
    db2 = DatabaseManager(db_path_2)
    db2.init_db()

    try:
        # Import into blank database
        db2.import_from_json(str(backup_path))
        imported_tasks = db2.get_all_tasks()
        assert len(imported_tasks) == 2

        # Verify details
        subjects = [t.subject for t in imported_tasks]
        assert "Math" in subjects
        assert "English" in subjects
    finally:
        db2.close()


def test_get_task_by_id(db):
    task = Task(
        subject="География",
        description="Карта мира",
        deadline="2026-06-03",
        effort_score=2,
        tags=["Карта"],
        status=TaskStatus.TODO,
    )
    task_id = db.add_task(task)

    # Test finding existing task
    db_task = db.get_task_by_id(task_id)
    assert db_task is not None
    assert db_task.subject == "География"
    assert db_task.tags == ["Карта"]

    # Test finding non-existent task
    assert db.get_task_by_id(99999) is None


def test_bot_user_registration(db):
    # Initial users should be empty
    assert len(db.get_all_users()) == 0

    # Register users
    db.register_user(123456)
    db.register_user(789012)
    # Register duplicate should be ignored
    db.register_user(123456)

    users = db.get_all_users()
    assert len(users) == 2
    assert 123456 in users
    assert 789012 in users

    # Unregister user
    success = db.unregister_user(123456)
    assert success is True
    assert len(db.get_all_users()) == 1

    # Unregister non-existent
    assert db.unregister_user(999999) is False


def test_add_and_get_task_with_grade(db):
    task = Task(
        subject="Физика",
        description="Лабораторная",
        deadline="2026-06-02",
        effort_score=5,
        tags=["Лаба"],
        status=TaskStatus.DONE,
        grade=5,
    )
    task_id = db.add_task(task)
    db_task = db.get_task_by_id(task_id)
    assert db_task is not None
    assert db_task.grade == 5


def test_many_to_many_tags(db):
    task1 = Task(
        subject="Физика",
        description="Лаба",
        deadline="2026-06-02",
        effort_score=5,
        tags=["Лаба", "Эксперимент"],
        status=TaskStatus.TODO,
    )
    task2 = Task(
        subject="Химия",
        description="Опыты",
        deadline="2026-06-03",
        effort_score=3,
        tags=["Эксперимент", "Химия"],
        status=TaskStatus.TODO,
    )
    t1_id = db.add_task(task1)
    t2_id = db.add_task(task2)

    # Check tags are shared in the db
    with db._connection() as conn:
        tags = [r["name"] for r in conn.execute("SELECT name FROM tags").fetchall()]
        assert len(tags) == 3  # Лаба, Эксперимент, Химия
        assert "Лаба" in tags
        assert "Эксперимент" in tags
        assert "Химия" in tags

    # Update task1 to have fewer tags, check orphan tag cleanup
    task1.id = t1_id
    task1.tags = ["Лаба"]
    db.update_task(task1)

    with db._connection() as conn:
        tags = [r["name"] for r in conn.execute("SELECT name FROM tags").fetchall()]
        assert len(tags) == 3

    # Delete task2, now "Эксперимент" and "Химия" should be orphaned and deleted
    db.delete_task(t2_id)

    with db._connection() as conn:
        tags = [r["name"] for r in conn.execute("SELECT name FROM tags").fetchall()]
        assert len(tags) == 1  # Only "Лаба" remains
        assert tags[0] == "Лаба"


def test_update_task_grade(db):
    task = Task(
        subject="Литература",
        description="Стих",
        deadline="2026-06-03",
        effort_score=2,
        tags=[],
        status=TaskStatus.DONE,
        grade=None,
    )
    task_id = db.add_task(task)

    # Initially grade is None
    db_task = db.get_task_by_id(task_id)
    assert db_task.grade is None

    # Update grade to 4
    success = db.update_task_grade(task_id, 4)
    assert success is True

    db_task = db.get_task_by_id(task_id)
    assert db_task.grade == 4

    # Clear grade back to None
    success = db.update_task_grade(task_id, None)
    assert success is True

    db_task = db.get_task_by_id(task_id)
    assert db_task.grade is None


def test_rotate_local_backups(db):
    # Create some dummy files in the backups folder
    backups_dir = db.db_path.parent / "backups"
    if backups_dir.exists():
        shutil.rmtree(backups_dir)
    backups_dir.mkdir(parents=True, exist_ok=True)

    # Create 7 dummy backup files with distinct modification times
    start_time = 1000000000
    for i in range(7):
        filepath = backups_dir / f"planner_backup_20260529_12000{i}_000000.db"
        filepath.touch()
        os.utime(filepath, (start_time + i, start_time + i))

    # Call rotate once to trigger rotation
    db.rotate_local_backups()

    backups = list(backups_dir.glob("planner_backup_*.db"))
    # Rotation should cap existing backups to exactly 5 files!
    assert len(backups) == 5

    # Clean up
    if backups_dir.exists():
        shutil.rmtree(backups_dir)


def test_import_from_json_preserves_grades(db, tmp_path):
    task_data = [
        {
            "subject": "Физика",
            "description": "Лабораторная",
            "deadline": "2026-06-02",
            "effort_score": 5,
            "tags": ["Лаба"],
            "status": 2,
            "grade": 5,
        },
        {
            "subject": "Химия",
            "description": "ДЗ",
            "deadline": "2026-06-03",
            "effort_score": 3,
            "tags": [],
            "status": 1,
            "grade": None,
        },
    ]
    backup_path = tmp_path / "temp_backup_grades.json"
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(task_data, f)

    try:
        db.import_from_json(str(backup_path))
        tasks = {t.subject: t for t in db.get_all_tasks()}
        assert len(tasks) == 2
        assert tasks["Физика"].grade == 5
        assert tasks["Химия"].grade is None
    finally:
        if backup_path.exists():
            backup_path.unlink()


def test_import_from_json_single_notify(db, tmp_path):
    task_data = [
        {
            "subject": "Физика",
            "description": "Лабораторная",
            "deadline": "2026-06-02",
            "effort_score": 5,
            "tags": ["Лаба"],
            "status": 2,
        },
        {
            "subject": "Химия",
            "description": "ДЗ",
            "deadline": "2026-06-03",
            "effort_score": 3,
            "tags": [],
            "status": 1,
        },
    ]
    backup_path = tmp_path / "temp_backup_notify.json"
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(task_data, f)

    original_notify = db._notify_change
    db._notify_change = MagicMock()

    try:
        db.import_from_json(str(backup_path))
        # Should be called exactly once at the end, not twice
        db._notify_change.assert_called_once()
    finally:
        db._notify_change = original_notify
        if backup_path.exists():
            backup_path.unlink()


def test_sql_aggregation_and_filters(db):
    from datetime import date, timedelta

    today = date.today()
    d_today = today.isoformat()
    d_tomorrow = (today + timedelta(days=1)).isoformat()
    d_past = (today - timedelta(days=10)).isoformat()

    # Insert test tasks
    t1 = Task(
        subject="Математика",
        description="Домашка 1",
        deadline=d_today,
        effort_score=4,
        tags=["ДЗ"],
        status=TaskStatus.TODO,
    )
    t2 = Task(
        subject="Физика",
        description="Лаба 2",
        deadline=d_today,
        effort_score=6,
        tags=["Лаба"],
        status=TaskStatus.DOING,
    )
    t3 = Task(
        subject="Химия",
        description="Опыт",
        deadline=d_tomorrow,
        effort_score=3,
        tags=["ДЗ", "Химия"],
        status=TaskStatus.DONE,
        grade=5,
    )
    t4 = Task(
        subject="Математика",
        description="Контрольная",
        deadline=d_past,
        effort_score=8,
        tags=["Контрольная"],
        status=TaskStatus.TODO,
    )  # Overdue

    db.add_task(t1)
    db.add_task(t2)
    db.add_task(t3)
    db.add_task(t4)

    # 1. Test get_filtered_tasks
    res = db.get_filtered_tasks(search_query="домашка")
    assert len(res) == 1
    assert res[0].subject == "Математика"

    res_tag = db.get_filtered_tasks(tag="ДЗ")
    assert len(res_tag) == 2

    res_status = db.get_filtered_tasks(status=TaskStatus.DONE)
    assert len(res_status) == 1
    assert res_status[0].subject == "Химия"

    res_sorted = db.get_filtered_tasks(sort_by="effort")
    assert res_sorted[0].effort_score == 8

    # 2. Test get_daily_load_for_date
    load, overloaded = db.get_daily_load_for_date(d_today)
    # t1 and t2 have deadline today and are TODO/DOING. Total: 4 + 6 = 10. Limit is 10.
    assert load == 10
    assert overloaded is False

    # 3. Test get_kpi_stats
    kpis = db.get_kpi_stats()
    assert kpis["total"] == 4
    assert kpis["completed"] == 1
    assert kpis["overdue"] == 1  # t4 is overdue and not done

    # 4. Test loads
    sub_load = db.get_subject_load()
    assert sub_load.get("Математика") == 12  # t1 (4) + t4 (8)
    assert sub_load.get("Физика") == 6
    assert "Химия" not in sub_load  # Химия is done

    tag_load = db.get_tag_load()
    assert tag_load.get("ДЗ") == 4  # Only t1 is active
    assert tag_load.get("Лаба") == 6

    # 5. Test grades
    grades = db.get_grades_stats()
    assert grades["total_count"] == 1
    assert grades["gpa"] == 5.0
    assert grades["count_5"] == 1

    subj_gpa = db.get_subject_grades_gpa()
    assert "Химия" in subj_gpa
    assert subj_gpa["Химия"]["gpa"] == 5.0

    # 6. Test overdue and date queries
    overdue_tasks = db.get_overdue_tasks(d_today)
    assert len(overdue_tasks) == 1
    assert overdue_tasks[0].subject == "Математика"

    date_tasks = db.get_tasks_by_date(d_today)
    assert len(date_tasks) == 2


def test_priority_sorting_sql(db):
    from datetime import date, timedelta

    today = date.today()
    d2 = (today + timedelta(days=2)).isoformat()

    t1 = Task(subject="Math", description="T1", deadline=d2, effort_score=4, tags=[])
    t2 = Task(subject="Physics", description="T2", deadline=d2, effort_score=8, tags=[])
    t3 = Task(
        subject="Chemistry",
        description="T3",
        deadline=d2,
        effort_score=4,
        tags=["Экзамен"],
    )

    db.add_task(t1)
    db.add_task(t2)
    db.add_task(t3)

    # Sort by priority
    tasks = db.get_filtered_tasks(sort_by="priority")

    assert len(tasks) == 3
    # Expected order: t2 (2.67), t3 (2.0), t1 (1.33)
    assert tasks[0].subject == "Physics"
    assert tasks[1].subject == "Chemistry"
    assert tasks[2].subject == "Math"
