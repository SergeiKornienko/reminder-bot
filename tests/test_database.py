import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
import database


def test_add_reminder(httpx_mock):
    """Добавление напоминалки вызывает правильный POST-запрос."""
    httpx_mock.add_response(
        method="POST",
        url="https://test.supabase.co/rest/v1/reminders",
        json=[{"id": 1}],
        status_code=201
    )

    database.SUPABASE_URL = "https://test.supabase.co"
    database.SUPABASE_KEY = "test-key"

    dt = datetime(2026, 6, 9, 10, 0, 0, tzinfo=timezone.utc)
    rid = database.add_reminder(None, 12345, "тест", dt)
    assert rid == 1


def test_get_due_reminders(monkeypatch):
    """Просроченные напоминалки возвращаются."""

    class FakeResponse:
        def __init__(self):
            self.status_code = 200

        def json(self):
            return [{"id": 1, "chat_id": 111, "remind_text": "прошлое"}]

        def raise_for_status(self):
            pass

    def fake_get(url, headers=None, params=None):
        return FakeResponse()

    monkeypatch.setattr(database.httpx, "get", fake_get)

    due = database.get_due_reminders(None)
    assert len(due) == 1
    assert due[0][2] == "прошлое"


def test_delete_reminder(monkeypatch):
    """Удаление вызывает DELETE-запрос и не падает."""

    class FakeResponse:
        def __init__(self):
            self.status_code = 200

        def json(self):
            return []

        def raise_for_status(self):
            pass

    def fake_delete(url, headers=None):
        # Проверяем, что URL содержит правильный id
        assert "eq.1" in url, f"URL должен содержать eq.1, но: {url}"
        return FakeResponse()

    monkeypatch.setattr(database.httpx, "delete", fake_delete)

    # Не должно бросать исключений
    database.delete_reminder(None, 1)


def test_get_reminders_by_chat(monkeypatch):
    """Фильтрация по chat_id работает."""

    class FakeResponse:
        def __init__(self):
            self.status_code = 200

        def json(self):
            return [
                {"remind_text": "для 111", "remind_time": "2026-06-09T10:00:00+00:00"},
            ]

        def raise_for_status(self):
            pass

    def fake_get(url, headers=None, params=None):
        return FakeResponse()

    monkeypatch.setattr(database.httpx, "get", fake_get)

    reminders = database.get_reminders_by_chat(None, 111)
    assert len(reminders) == 1
    assert reminders[0][0] == "для 111"
