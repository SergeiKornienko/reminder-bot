import re
import asyncio
from datetime import datetime, timedelta
import sqlite3
import dateparser
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- БАЗА ДАННЫХ ---
conn = sqlite3.connect('reminders.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS reminders
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   chat_id INTEGER NOT NULL,
                   remind_text TEXT NOT NULL,
                   remind_time TIMESTAMP NOT NULL)''')
conn.commit()

# --- ОБРАБОТЧИК СООБЩЕНИЙ ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.message.chat_id

    if not user_text.lower().startswith("напомни"):
        await update.message.reply_text(
            "Я понимаю только команды вроде:\n"
            "«Напомни завтра в 10:00 купить хлеб»\n"
            "«Напомни 15.06.2026 в 14:30 позвонить врачу»\n"
            "«Напомни через 2 часа проверить почту»"
        )
        return

    payload = user_text[7:].strip()
    remind_dt = None
    remind_text = payload

    # Паттерн: "завтра/послезавтра/сегодня в ЧЧ:ММ"
    day_match = re.match(
        r'(сегодня|завтра|послезавтра)\s+в\s+(\d{1,2}):(\d{2})\s*(.*)',
        payload, re.IGNORECASE
    )
    if day_match:
        day_word = day_match.group(1).lower()
        hour = int(day_match.group(2))
        minute = int(day_match.group(3))
        remind_text = day_match.group(4).strip() or payload

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
            r'(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?\s+в\s+(\d{1,2}):(\d{2})\s*(.*)',
            payload
        )
        if date_match:
            day = int(date_match.group(1))
            month = int(date_match.group(2))
            year = int(date_match.group(3)) if date_match.group(3) else datetime.now().year
            hour = int(date_match.group(4))
            minute = int(date_match.group(5))
            remind_text = date_match.group(6).strip() or payload
            try:
                remind_dt = datetime(year, month, day, hour, minute)
            except ValueError:
                pass

    # Паттерн: "через X часов/минут"
    if remind_dt is None:
        relative_match = re.match(
            r'через\s+(\d+)\s+(час|часа|часов|минут|минуту|минуты)\s*(.*)',
            payload, re.IGNORECASE
        )
        if relative_match:
            amount = int(relative_match.group(1))
            unit = relative_match.group(2).lower()
            remind_text = relative_match.group(3).strip() or payload
            now = datetime.now()
            if "час" in unit:
                remind_dt = now + timedelta(hours=amount)
            elif "минут" in unit:
                remind_dt = now + timedelta(minutes=amount)

    # Запасной: dateparser
    if remind_dt is None:
        remind_dt = dateparser.parse(payload, languages=['ru'])

    # Если вообще ничего не поняли
    if remind_dt is None:
        await update.message.reply_text(
            "❌ Не смог понять дату и время.\n\n"
            "Попробуй один из форматов:\n"
            "• Напомни завтра в 10:00 купить хлеб\n"
            "• Напомни 15.06.2026 в 14:30 позвонить врачу\n"
            "• Напомни через 2 часа проверить почту"
        )
        return

    # Сохранение
    cursor.execute(
        "INSERT INTO reminders (chat_id, remind_text, remind_time) VALUES (?, ?, ?)",
        (chat_id, remind_text, remind_dt)
    )
    conn.commit()

    formatted_time = remind_dt.strftime("%d.%m.%Y в %H:%M")
    await update.message.reply_text(f"✅ Запомнил! Напомню {formatted_time}:\n«{remind_text}»")

# --- ФОНОВЫЙ ПРОВЕРЯЛЬЩИК ---
async def check_reminders(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    cursor.execute("SELECT id, chat_id, remind_text FROM reminders WHERE remind_time <= ?", (now,))
    due_reminders = cursor.fetchall()

    for rem_id, chat_id, text in due_reminders:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⏰ НАПОМИНАНИЕ!\n«{text}»"
            )
        except Exception as e:
            print(f"Ошибка отправки: {e}")

        cursor.execute("DELETE FROM reminders WHERE id = ?", (rem_id,))
        conn.commit()

# --- КОМАНДА /LIST (исправленная) ---
async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    cursor.execute(
        "SELECT remind_text, remind_time FROM reminders WHERE chat_id = ? ORDER BY remind_time",
        (chat_id,)
    )
    reminders = cursor.fetchall()

    if not reminders:
        await update.message.reply_text("У тебя нет активных напоминалок.")
        return

    msg = "📋 Твои напоминалки:\n\n"
    for text, dt in reminders:
        # dt может быть строкой (из базы) или datetime (если адаптер сработал)
        if isinstance(dt, str):
            # Обрезаем микросекунды, если они есть: "2026-06-05 22:17:00.275747" -> "2026-06-05 22:17:00"
            if '.' in dt:
                dt = dt.split('.')[0]
            dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        formatted = dt.strftime("%d.%m в %H:%M")
        msg += f"• {formatted} — {text}\n"

    await update.message.reply_text(msg)

# --- ТОЧКА ВХОДА ---
def main():
    TOKEN = "8828207782:AAEoiV3p4M3i9LinRDkBMXZYowX04waZRd8"

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("list", list_reminders))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    job_queue = app.job_queue
    job_queue.run_repeating(check_reminders, interval=60, first=10)

    print("Бот запущен. Напряги процессор, малыш.")
    app.run_polling()

if __name__ == '__main__':
    main()
