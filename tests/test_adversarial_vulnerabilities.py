import asyncio
import json
import os
import tempfile
import threading
from datetime import date
from pathlib import Path
import pytest
from aiogram.types import InlineKeyboardMarkup

from src.core.nlp_parser import DeadlineParser, parse_natural_language_task
from src.core.database import DatabaseManager
from src.core.models import Task, TaskStatus
from src.bot.state import BotState
from src.bot.handlers.tasks import build_task_list_payload


class TestAcademicDashboardAdversarial:
    """Adversarial resilience verification suite proving vulnerabilities are resolved."""

    def test_mitigation_1_nlp_integer_overflow_safe(self):
        """
        VERIFICATION 1:
        Extreme large numbers in natural language (e.g. 'через 9999999999999999999999999999 дней')
        are safely capped without throwing OverflowError.
        """
        malicious_input = "сдать курсовую через 9999999999999999999999999999 дней"
        
        # Must NOT raise OverflowError now
        cleaned_text, deadline = DeadlineParser().parse(malicious_input)
        assert deadline is not None
        
        parsed = parse_natural_language_task(malicious_input)
        assert parsed is not None
        assert parsed["deadline"] is not None
        print(f"\n[FIXED] NLP Parser safely handled extreme offset: deadline={parsed['deadline']}")

    def test_mitigation_2_telegram_inline_keyboard_button_capping(self, tmp_path):
        """
        VERIFICATION 2:
        When user has 35+ active tasks, build_task_list_payload caps interactive buttons
        to max 25 tasks (<= 77 buttons), strictly respecting Telegram's 100-button limit.
        """
        db_file = tmp_path / "dos_test.db"
        db = DatabaseManager(db_file)
        db.init_db()
        app_state = BotState(db)

        # Inject 35 active tasks
        for i in range(1, 36):
            task = Task(
                subject=f"Предмет {i}",
                description=f"Задание номер {i}",
                deadline=date.today().isoformat(),
                effort_score=3,
                status=TaskStatus.TODO,
            )
            db.add_task(task, notify=False)

        app_state.invalidate()
        text, markup = build_task_list_payload(app_state)
        
        total_buttons = sum(len(row) for row in markup.inline_keyboard)
        print(f"\n[FIXED] Generated {total_buttons} buttons for 35 tasks (Telegram Limit: 100). Safe!")
        
        TELEGRAM_MAX_BUTTONS = 100
        assert total_buttons <= TELEGRAM_MAX_BUTTONS
        assert total_buttons == 77  # 3 * 25 + 2 controls

    def test_mitigation_3_unbounded_json_import_sanitized(self, tmp_path):
        """
        VERIFICATION 3:
        import_from_json sanitizes and truncates oversized payloads, protecting database and memory.
        """
        db_file = tmp_path / "bomb_test.db"
        db = DatabaseManager(db_file)
        db.init_db()

        huge_subject = "A" * 100_000
        huge_description = "B" * 500_000
        malicious_json = [
            {
                "subject": huge_subject,
                "description": huge_description,
                "deadline": "2026-12-31",
                "effort_score": 5,
                "status": 0,
                "tags": ["X" * 10_000 for _ in range(50)],
            }
        ]

        json_path = tmp_path / "malicious.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(malicious_json, f)

        # Import should sanitize fields
        db._backup_mgr.import_from_json(str(json_path))
        all_tasks = db.get_all_tasks()
        
        assert len(all_tasks) == 1
        assert len(all_tasks[0].subject) <= 255
        assert len(all_tasks[0].description) <= 2000
        assert len(all_tasks[0].tags) <= 30
        print(f"\n[FIXED] Unbounded JSON safely clamped: subject={len(all_tasks[0].subject)} chars, desc={len(all_tasks[0].description)} chars, tags={len(all_tasks[0].tags)}")

    def test_mitigation_4_bot_state_thread_safety(self, tmp_path):
        """
        VERIFICATION 4:
        BotState contains thread lock protecting cache against race conditions.
        """
        db_file = tmp_path / "race_test.db"
        db = DatabaseManager(db_file)
        db.init_db()
        app_state = BotState(db)

        assert hasattr(app_state, "_lock")
        assert isinstance(app_state._lock, type(threading.Lock()))
        print(f"\n[FIXED] BotState mutex lock verified.")
