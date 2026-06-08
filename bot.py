import os
import sys
import threading
import asyncio
from flask import Flask
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from database import get_connection, init_db
from handlers import handle_message, check_reminders, list_reminders

# --- Конфигурация ---
TOKEN = os.environ.get("BOT_TOKEN")

def check_token():
    if not TOKEN:
        print("❌ ОШИБКА: Переменная BOT_TOKEN не найдена!", file=sys.stderr)
        sys.exit(1)
    print(f"✅ Токен загружен (длина: {len(TOKEN)})", file=sys.stderr)

# --- Flask ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is alive"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# --- Точка входа ---
if __name__ == '__main__':
    check_token()

    # База данных
    conn = get_connection()
    init_db(conn)

    # Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Бот
    app = Application.builder().token(TOKEN).build()
    app.bot_data["db_conn"] = conn  # Передаём соединение в обработчики

    app.add_handler(CommandHandler("list", list_reminders))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    job_queue = app.job_queue
    job_queue.run_repeating(check_reminders, interval=60, first=10)

    print("Бот + Flask на Render. Погнали!", file=sys.stderr, flush=True)
    app.run_polling(stop_signals=[])
