import re
import sys
from datetime import datetime, timedelta
import dateparser


def parse_reminder(text: str):
    """
    Пытается извлечь дату и текст напоминалки из сообщения.
    Возвращает:
      (datetime, remind_text) — если успешно
      (None, payload)         — если не удалось распарсить
    """
    payload = text.strip()
    remind_dt = None
    remind_text = payload

    # Паттерн: "завтра/послезавтра/сегодня в ЧЧ:ММ"
    day_match = re.match(
        r'(сегодня|завтра|послезавтра)\s+в\s+(\d{1,2}):(\d{2})(?:\s+(.*))?',
        payload, re.IGNORECASE
    )
    if day_match:
        day_word = day_match.group(1).lower()
        hour = int(day_match.group(2))
        minute = int(day_match.group(3))
        remind_text = day_match.group(4) if day_match.group(4) else payload
        now = datetime.now().replace(second=0, microsecond=0)
        if day_word == "сегодня":
            remind_dt = now.replace(hour=hour, minute=minute)
        elif day_word == "завтра":
            remind_dt = now.replace(hour=hour, minute=minute) + timedelta(days=1)
        elif day_word == "послезавтра":
            remind_dt = now.replace(hour=hour, minute=minute) + timedelta(days=2)

    # Паттерн: "ДД.ММ.ГГГГ в ЧЧ:ММ" или "ДД.ММ в ЧЧ:ММ"
    if remind_dt is None:
        date_match = re.match(
            r'(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?\s+в\s+(\d{1,2}):(\d{2})(?:\s+(.*))?',
            payload
        )
        if date_match:
            day = int(date_match.group(1))
            month = int(date_match.group(2))
            year = int(date_match.group(3)) if date_match.group(3) else datetime.now().year
            hour = int(date_match.group(4))
            minute = int(date_match.group(5))
            remind_text = date_match.group(6) if date_match.group(6) else payload
            try:
                remind_dt = datetime(year, month, day, hour, minute)
            except ValueError:
                pass

    # Паттерн: "через X часов/минут"
    if remind_dt is None:
        relative_match = re.match(
            r'через\s+(\d+)\s+(часов|часа|час|минут|минуту|минуты)(?:\s+(.*))?',
            payload, re.IGNORECASE
        )
        if relative_match:
            amount = int(relative_match.group(1))
            unit = relative_match.group(2).lower()
            remind_text = relative_match.group(3) if relative_match.group(3) else payload
            now = datetime.now()
            if "час" in unit:
                remind_dt = now + timedelta(hours=amount)
            elif "минут" in unit:
                remind_dt = now + timedelta(minutes=amount)

    # Запасной: dateparser
    if remind_dt is None:
        remind_dt = dateparser.parse(payload, languages=['ru'])

    if remind_dt is None:
        return (None, payload)

    return (remind_dt, remind_text)
