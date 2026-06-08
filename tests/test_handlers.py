import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from handlers import handle_message, list_reminders


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
