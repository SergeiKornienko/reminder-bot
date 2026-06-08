import os
from datetime import datetime, timezone
import httpx

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def _url(table: str) -> str:
    return f"{SUPABASE_URL}/rest/v1/{table}"

def add_reminder(client, chat_id: int, remind_text: str, remind_time: datetime):
    """Добавляет напоминалку. Возвращает id новой записи."""
    data = {
        "chat_id": chat_id,
        "remind_text": remind_text,
        "remind_time": remind_time.isoformat()
    }
    response = httpx.post(
        _url("reminders"),
        headers=HEADERS,
        json=data
    )
    response.raise_for_status()
    return response.json()[0]["id"]

def get_due_reminders(client):
    """Возвращает список напоминалок, которые пора отправить."""
    now = datetime.now(timezone.utc).isoformat()
    response = httpx.get(
        _url("reminders"),
        headers=HEADERS,
        params={
            "select": "id,chat_id,remind_text",
            "remind_time": f"lte.{now}",
            "order": "remind_time.asc"
        }
    )
    response.raise_for_status()
    data = response.json()
    return [(r["id"], r["chat_id"], r["remind_text"]) for r in data]

def delete_reminder(client, reminder_id: int):
    """Удаляет напоминалку по id."""
    response = httpx.delete(
        f"{_url('reminders')}?id=eq.{reminder_id}",
        headers=HEADERS
    )
    response.raise_for_status()

def get_reminders_by_chat(client, chat_id: int):
    """Возвращает все напоминалки для конкретного чата."""
    url = f"{_url('reminders')}?select=remind_text,remind_time&chat_id=eq.{chat_id}&order=remind_time.asc"
    response = httpx.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return [(r["remind_text"], r["remind_time"]) for r in data]
