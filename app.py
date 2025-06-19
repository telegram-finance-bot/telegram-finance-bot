import os
import json
import gspread
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound

# Лог
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Проверка переменных
def check_env():
    for key in ["BOT_TOKEN", "SHEET_ID", "CREDS_FILE", "WEBHOOK_URL", "PORT"]:
        if not os.getenv(key):
            raise Exception(f"❌ Нет переменной окружения: {key}")
    if not os.path.exists(os.getenv("CREDS_FILE")):
        raise Exception("❌ CREDS_FILE не найден")

# Подключение Google Sheets
def init_sheets():
    with open(os.getenv("CREDS_FILE")) as f:
        data = json.load(f)
    creds = Credentials.from_service_account_info(data, scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file"
    ])
    client = gspread.authorize(creds)
    sheet = client.open_by_key(os.getenv("SHEET_ID"))
    logger.info(f"✅ Подключено к таблице: {sheet.title}")
    for name in ["GIM", "TR"]:
        try:
            sheet.worksheet(name)
        except WorksheetNotFound:
            sheet.add_worksheet(title=name, rows=100, cols=20)
    return sheet

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен ✅")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start — запуск\n/help — помощь")

# Запуск
async def main():
    check_env()
    sheet = init_sheets()

    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.bot_data["sheet"] = sheet
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    await app.initialize()
    await app.start()
    await app.bot.set_webhook(url=os.getenv("WEBHOOK_URL"))
    logger.info("🚀 Webhook установлен")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
