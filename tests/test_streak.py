"""Tests for GET /habits/{id}/streak (task 1)."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


@pytest.fixture
def today(monkeypatch):
    pinned = date(2026, 9, 25)
    monkeypatch.setattr(main, "_today", lambda: pinned)
    return pinned


def _habit(name: str = "Read 20 minutes") -> int:
    response = client.post("/habits", json={"name": name})
    assert response.status_code == 200
    return response.json()["id"]


def _checkin(habit_id: int, day: date) -> None:
    response = client.post(f"/habits/{habit_id}/checkin", json={"day": day.isoformat()})
    assert response.status_code == 200


def test_streak_counts_consecutive_days_ending_today(today):
    habit_id = _habit()
    for offset in range(3):
        _checkin(habit_id, today - timedelta(days=offset))

    response = client.get(f"/habits/{habit_id}/streak")

    assert response.status_code == 200
    assert response.json() == {"habit_id": habit_id, "streak": 3}


def test_streak_is_zero_without_any_checkin(today):
    habit_id = _habit()

    response = client.get(f"/habits/{habit_id}/streak")

    assert response.status_code == 200
    assert response.json()["streak"] == 0


def test_streak_unknown_habit_is_404(today):
    response = client.get("/habits/99999/streak")

    assert response.status_code == 404


def test_streak_stops_at_a_gap(today):
    habit_id = _habit()
    _checkin(habit_id, today)
    _checkin(habit_id, today - timedelta(days=1))
    _checkin(habit_id, today - timedelta(days=3))  # the gap

    assert client.get(f"/habits/{habit_id}/streak").json()["streak"] == 2


def test_streak_is_zero_when_today_is_missing(today):
    habit_id = _habit()
    _checkin(habit_id, today - timedelta(days=1))

    assert client.get(f"/habits/{habit_id}/streak").json()["streak"] == 0


def test_streak_duplicate_day_counts_once(today):
    habit_id = _habit()
    _checkin(habit_id, today)
    _checkin(habit_id, today)
    _checkin(habit_id, today - timedelta(days=1))

    assert client.get(f"/habits/{habit_id}/streak").json()["streak"] == 2


def test_streak_survives_unparsable_row(today):
    """Task 2 (validation) is not implemented, so junk can reach the table."""
    habit_id = _habit()
    _checkin(habit_id, today)
    with main.get_db() as conn:
        conn.execute(
            "INSERT INTO checkins (habit_id, day) VALUES (?, ?)",
            (habit_id, "not-a-date"),
        )
        conn.commit()

    response = client.get(f"/habits/{habit_id}/streak")

    assert response.status_code == 200
    assert response.json()["streak"] == 1
