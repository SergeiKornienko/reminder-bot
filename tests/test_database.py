import sys
sys.path.insert(0, '/data/data/com.termux/files/home/health')

import os
import tempfile
from datetime import datetime, timedelta
import database


def setup_function():
    """Перед каждым тестом: создаём временную базу."""
    database.DB_PATH = os.path.join(tempfile.gettempdir(), 'test_reminders.db')
    conn = database.get_connection()
    database.init_db(conn)
    conn.close()


def teardown_function():
    """После каждого теста: удаляем временную базу."""
    if os.path.exists(database.DB_PATH):
        os.remove(database.DB_PATH)


def test_init_db():
    """Таблица создаётся без ошибок."""
    conn = database.get_connection()
    database.init_db(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reminders'")
    assert cursor.fetchone() is not None
    conn.close()


def test_add_reminder():
    """Добавление напоминалки возвращает id > 0."""
    conn = database.get_connection()
    database.init_db(conn)
    dt = datetime.now() + timedelta(hours=1)
    rid = database.add_reminder(conn, 12345, "тест", dt)
    assert rid > 0
    conn.close()


def test_get_due_reminders():
    """Просроченная напоминалка возвращается, будущая — нет."""
    conn = database.get_connection()
    database.init_db(conn)

    past = datetime.now() - timedelta(hours=1)
    future = datetime.now() + timedelta(hours=1)

    database.add_reminder(conn, 111, "прошлое", past)
    database.add_reminder(conn, 222, "будущее", future)

    due = database.get_due_reminders(conn)
    assert len(due) == 1
    assert due[0][2] == "прошлое"
    conn.close()


def test_delete_reminder():
    """Удаление работает."""
    conn = database.get_connection()
    database.init_db(conn)

    dt = datetime.now() + timedelta(hours=1)
    rid = database.add_reminder(conn, 999, "удалить", dt)
    database.delete_reminder(conn, rid)

    due = database.get_due_reminders(conn)
    assert len(due) == 0
    conn.close()


def test_get_reminders_by_chat():
    """Фильтрация по chat_id работает."""
    conn = database.get_connection()
    database.init_db(conn)

    dt = datetime.now() + timedelta(hours=1)
    database.add_reminder(conn, 111, "для 111", dt)
    database.add_reminder(conn, 222, "для 222", dt)

    r111 = database.get_reminders_by_chat(conn, 111)
    r222 = database.get_reminders_by_chat(conn, 222)
    r999 = database.get_reminders_by_chat(conn, 999)

    assert len(r111) == 1
    assert r111[0][0] == "для 111"
    assert len(r222) == 1
    assert len(r999) == 0
    conn.close()
