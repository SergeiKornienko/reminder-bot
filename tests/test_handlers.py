import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from handlers import handle_message, list_reminders


class FakeResponse:
    def __init__(self, json_data=None, status_code=201):
        self._json = json_data or []
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        pass


class FakeMessage:
    def __init__(self, text, chat_id=12345):
        self.text = text
        self.chat_id = chat_id
        self._reply = None

    async def reply_text(self, text):
        self._reply = text


class FakeUpdate:
    def __init__(self, text, chat_id=12345):
        self.message = FakeMessage(text, chat_id)


class FakeContext:
    def __init__(self):
        self.bot_data = {}


@pytest.mark.asyncio
async def test_handle_message_not_reminder():
    update = FakeUpdate("привет бот")
    context = FakeContext()
    await handle_message(update, context)
    assert update.message._reply is not None
    assert "Я понимаю только" in update.message._reply


@pytest.mark.asyncio
async def test_handle_message_bad_date():
    update = FakeUpdate("напомни блаблабла")
    context = FakeContext()
    await handle_message(update, context)
    assert update.message._reply is not None
    assert "Не смог понять дату" in update.message._reply


@pytest.mark.asyncio
async def test_handle_message_valid(monkeypatch):
    """Корректная напоминалка добавляется."""
    import database

    def fake_post(url, headers=None, json=None):
        return FakeResponse(json_data=[{"id": 1}])

    monkeypatch.setattr(database.httpx, "post", fake_post)

    update = FakeUpdate("напомни завтра в 10:00 купить хлеб")
    context = FakeContext()
    context.bot_data["db_client"] = None

    await handle_message(update, context)
    assert update.message._reply is not None
    assert "✅ Запомнил!" in update.message._reply


@pytest.mark.asyncio
async def test_list_reminders_empty(monkeypatch):
    """Пустой список напоминалок."""
    import database

    def fake_get(url, headers=None, params=None):
        return FakeResponse(json_data=[], status_code=200)

    monkeypatch.setattr(database.httpx, "get", fake_get)

    update = FakeUpdate("/list")
    context = FakeContext()
    context.bot_data["db_client"] = None

    await list_reminders(update, context)
    assert update.message._reply is not None
    assert "нет активных напоминалок" in update.message._reply
