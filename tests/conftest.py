import os

import pytest

from src.core.database import DatabaseManager


@pytest.fixture
def db(tmp_path):
    """Fixture providing an isolated database instance for testing."""
    db_path = tmp_path / "test_db.sqlite"
    db_manager = DatabaseManager(db_path)
    db_manager.init_db()
    yield db_manager
    db_manager.close()
    for suffix in ("", "-wal", "-shm"):
        path = db_path.with_name(db_path.name + suffix)
        if path.exists():
            try:
                os.remove(path)
            except OSError:
                pass
