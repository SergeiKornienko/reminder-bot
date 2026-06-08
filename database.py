import sqlite3
from datetime import datetime

DB_PATH = 'reminders.db'

def get_connection():
    """Создаёт подключение к базе (по одному на вызов — для тестов)."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def init_db(conn):
    """Создаёт таблицу, если её нет."""
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS reminders
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       chat_id INTEGER NOT NULL,
                       remind_text TEXT NOT NULL,
                       remind_time TIMESTAMP NOT NULL)''')
    conn.commit()

def add_reminder(conn, chat_id: int, remind_text: str, remind_time: datetime):
    """Добавляет напоминалку. Возвращает id новой записи."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reminders (chat_id, remind_text, remind_time) VALUES (?, ?, ?)",
        (chat_id, remind_text, remind_time)
    )
    conn.commit()
    return cursor.lastrowid

def get_due_reminders(conn):
    """Возвращает список напоминалок, которые пора отправить.
       Каждая запись — кортеж (id, chat_id, remind_text)."""
    now = datetime.now()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, chat_id, remind_text FROM reminders WHERE remind_time <= ?",
        (now,)
    )
    return cursor.fetchall()

def delete_reminder(conn, reminder_id: int):
    """Удаляет напоминалку по id."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    conn.commit()

def get_reminders_by_chat(conn, chat_id: int):
    """Возвращает все напоминалки для конкретного чата.
       Каждая запись — кортеж (remind_text, remind_time)."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT remind_text, remind_time FROM reminders WHERE chat_id = ? ORDER BY remind_time",
        (chat_id,)
    )
    return cursor.fetchall()
