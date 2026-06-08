import os
import sys
import time
import threading
import asyncio
import logging

from flask import Flask
from waitress import serve
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from handlers import handle_message, check_reminders, list_reminders

# --- Логирование ---
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Отключаем дебаг-логи от httpx и telegram
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

# --- Конфигурация ---
TOKEN = os.environ.get("BOT_TOKEN")

def check_token():
    if not TOKEN:
        logger.error("Переменная BOT_TOKEN не найдена!")
        sys.exit(1)
    logger.info("Токен загружен (длина: %d)", len(TOKEN))

# --- Flask ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is alive"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    logger.info("Запуск WSGI-сервера на порту %d", port)
    serve(web_app, host='0.0.0.0', port=port, _quiet=True)

# --- Точка входа ---
if __name__ == '__main__':
    check_token()

    # Flask/Waitress в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Бот
    app = Application.builder().token(TOKEN).build()
    app.bot_data["db_client"] = None

    app.add_handler(CommandHandler("list", list_reminders))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    job_queue = app.job_queue
    job_queue.run_repeating(check_reminders, interval=60, first=10)

    logger.info("Бот + Waitress + Supabase на Render. Погнали!")

    # Ждём, чтобы старый процесс Telegram точно отключился
    time.sleep(15)

    app.run_polling(stop_signals=[])
