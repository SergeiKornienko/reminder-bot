from parser import parse_reminder
from datetime import datetime, timedelta


def test_parse_tomorrow_morning():
    dt, text = parse_reminder("завтра в 10:00 купить хлеб")
    assert dt is not None
    assert text == "купить хлеб"
    expected = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    assert dt == expected


def test_parse_today():
    dt, text = parse_reminder("сегодня в 15:30 позвонить врачу")
    assert dt is not None
    assert text == "позвонить врачу"
    expected = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)
    assert dt == expected


def test_parse_relative_hours():
    dt, text = parse_reminder("через 2 часа проверить почту")
    assert dt is not None
    assert text == "проверить почту"


def test_parse_relative_minutes():
    dt, text = parse_reminder("через 5 минут тест")
    assert dt is not None
    assert text == "тест"


def test_parse_no_date():
    dt, text = parse_reminder("блаблабла без даты")
    assert dt is None


def test_parse_exact_date():
    dt, text = parse_reminder("15.06.2026 в 14:30 важная встреча")
    assert dt is not None
    assert text == "важная встреча"
    assert dt.year == 2026
    assert dt.month == 6
    assert dt.day == 15
    assert dt.hour == 14
    assert dt.minute == 30
