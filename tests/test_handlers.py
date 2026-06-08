import os
import tempfile
import pytest
import database
from handlers import handle_message, list_reminders


# --- Заглушки ---

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
    def __init__(self, conn):
        self.bot_data = {"db_conn": conn}


# --- Фикстуры ---

@pytest.fixture(autouse=True)
def setup_teardown():
    database.DB_PATH = os.path.join(tempfile.gettempdir(), 'test_handlers.db')
    conn = database.get_connection()
    database.init_db(conn)
    conn.close()
    yield
    if os.path.exists(database.DB_PATH):
        os.remove(database.DB_PATH)


# --- Тесты ---

@pytest.mark.asyncio
async def test_handle_message_valid():
    conn = database.get_connection()
    database.init_db(conn)
    update = FakeUpdate("напомни завтра в 10:00 купить хлеб")
    context = FakeContext(conn)
    await handle_message(update, context)
    reply = update.message._reply
    assert reply is not None
    assert "✅ Запомнил!" in reply
    assert "купить хлеб" in reply
    conn.close()


@pytest.mark.asyncio
async def test_handle_message_not_reminder():
    conn = database.get_connection()
    update = FakeUpdate("привет бот")
    context = FakeContext(conn)
    await handle_message(update, context)
    reply = update.message._reply
    assert reply is not None
    assert "Я понимаю только" in reply
    conn.close()


@pytest.mark.asyncio
async def test_handle_message_bad_date():
    conn = database.get_connection()
    update = FakeUpdate("напомни блаблабла")
    context = FakeContext(conn)
    await handle_message(update, context)
    reply = update.message._reply
    assert reply is not None
    assert "Не смог понять дату" in reply
    conn.close()


@pytest.mark.asyncio
async def test_list_reminders_empty():
    conn = database.get_connection()
    database.init_db(conn)
    update = FakeUpdate("/list")
    context = FakeContext(conn)
    await list_reminders(update, context)
    reply = update.message._reply
    assert reply is not None
    assert "нет активных напоминалок" in reply
    conn.close()
