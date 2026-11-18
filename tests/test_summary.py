"""Tests for GET /habits/{id}/summary (task 3)."""

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


def test_summary_counts_checkins_in_the_window(today):
    habit_id = _habit()
    for offset in (0, 2, 5):
        _checkin(habit_id, today - timedelta(days=offset))

    response = client.get(f"/habits/{habit_id}/summary")

    assert response.status_code == 200
    assert response.json()["count"] == 3


def test_summary_is_zero_without_checkins(today):
    habit_id = _habit()

    assert client.get(f"/habits/{habit_id}/summary").json()["count"] == 0
