import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from parser import parse_reminder
from database import add_reminder, get_due_reminders, delete_reminder, get_reminders_by_chat

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.message.chat_id

    if not user_text.lower().startswith("напомни"):
        await update.message.reply_text(
            "Я понимаю только:\n"
            "«Напомни завтра в 10:00 купить хлеб»\n"
            "«Напомни 15.06.2026 в 14:30 позвонить врачу»\n"
            "«Напомни через 2 часа проверить почту»"
        )
        return

    payload = user_text[7:].strip()
    remind_dt, remind_text = parse_reminder(payload)

    if remind_dt is None:
        await update.message.reply_text(
            "❌ Не смог понять дату и время.\n\n"
            "Форматы:\n"
            "• Напомни завтра в 10:00 ...\n"
            "• Напомни 15.06.2026 в 14:30 ...\n"
            "• Напомни через 2 часа ..."
        )
        return

    client = context.bot_data.get("db_client")
    add_reminder(client, chat_id, remind_text, remind_dt)
    formatted_time = remind_dt.strftime("%d.%m.%Y в %H:%M")
    await update.message.reply_text(f"✅ Запомнил! Напомню {formatted_time}:\n«{remind_text}»")


async def check_reminders(context: ContextTypes.DEFAULT_TYPE):
    client = context.bot_data.get("db_client")
    due_reminders = get_due_reminders(client)
    for rem_id, chat_id, text in due_reminders:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⏰ НАПОМИНАНИЕ!\n«{text}»"
            )
        except Exception as e:
            logger.warning("Ошибка отправки: %s", e)
        delete_reminder(client, rem_id)


async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    client = context.bot_data.get("db_client")
    reminders = get_reminders_by_chat(client, chat_id)

    if not reminders:
        await update.message.reply_text("У тебя нет активных напоминалок.")
        return

    msg = "📋 Твои напоминалки:\n\n"
    for text, dt in reminders:
        if isinstance(dt, str):
            dt = dt.replace("T", " ").split("+")[0].split(".")[0]
            dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        formatted = dt.strftime("%d.%m в %H:%M")
        msg += f"• {formatted} — {text}\n"
    await update.message.reply_text(msg)
