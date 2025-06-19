import os
import json
import gspread
import logging
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound

# Логгер
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Health-check endpoint
async def handle_health_check(request):
    return web.Response(text="OK", status=200)

# Проверка переменных окружения
def check_environment():
    required = ["BOT_TOKEN", "SHEET_ID", "CREDS_FILE", "WEBHOOK_URL", "PORT"]
    for key in required:
        if not os.environ.get(key):
            logger.error(f"❌ Отсутствует переменная: {key}")
            return False
    if not os.path.exists(os.environ["CREDS_FILE"]):
        logger.error("❌ CREDS_FILE не найден")
        return False
    return True

# Google Sheets
def init_google_sheets():
    try:
        with open(os.environ["CREDS_FILE"]) as f:
            creds_data = json.load(f)
        credentials = Credentials.from_service_account_info(
            creds_data,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(os.environ["SHEET_ID"])
        logger.info(f"📄 Подключено к таблице: {sheet.title}")
        for name in ["GIM", "TR"]:
            try:
                sheet.worksheet(name)
            except WorksheetNotFound:
                sheet.add_worksheet(title=name, rows=100, cols=20)
                logger.info(f"✅ Создан лист: {name}")
        return sheet
    except Exception as e:
        logger.error(f"❌ Ошибка Google Sheets: {e}")
        return None

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот работает! ✅")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start — запуск\n/help — помощь")

# Основной запуск
async def async_main():
    if not check_environment():
        raise RuntimeError("❌ Переменные окружения не настроены")

    sheet = init_google_sheets()
    if not sheet:
        raise RuntimeError("❌ Не удалось подключиться к Google Sheets")

    app = web.Application()
    app.add_routes([web.get("/", handle_health_check)])

    application = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).web_app(app).build()
    application.bot_data["sheet"] = sheet
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    await application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ["PORT"]),
        webhook_url=os.environ["WEBHOOK_URL"],
        drop_pending_updates=True
    )

if __name__ == "__main__":
    asyncio.run(async_main())
