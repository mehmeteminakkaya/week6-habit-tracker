"""Shared test setup: every test gets its own throwaway SQLite database.

The starter app keeps its database next to ``main.py``. Without this fixture the tests
share one file, so a habit created in one test can leak into the next and the suite
becomes order-dependent. ``main.get_db`` reads ``main.DB_PATH`` on every call, so
monkeypatching the constant is enough.
"""

import pytest

import main


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "habits.db")
    main.init_db()
    yield
