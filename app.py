import os
import json
import gspread
import logging
import asyncio
import nest_asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound

# ===== Логгер =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== Health Check =====
async def handle_health_check(request):
    return web.Response(text="OK", status=200)

async def start_health_server(port):
    app = web.Application()
    app.add_routes([web.get("/", handle_health_check)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health-check сервер запущен на порту {port}")

# ===== Проверка переменных окружения =====
def check_environment():
    required = ["BOT_TOKEN", "SHEET_ID", "CREDS_FILE", "WEBHOOK_URL", "PORT"]
    for key in required:
        if not os.environ.get(key):
            logger.error(f"❌ Отсутствует переменная окружения: {key}")
            return False
    if not os.path.exists(os.environ["CREDS_FILE"]):
        logger.error("❌ CREDS_FILE не найден")
        return False
    return True

# ===== Подключение к Google Sheets =====
def init_google_sheets():
    try:
        creds_file = os.environ.get("CREDS_FILE")
        sheet_id = os.environ.get("SHEET_ID")

        with open(creds_file) as f:
            creds_data = json.load(f)

        credentials = Credentials.from_service_account_info(
            creds_data,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.file"
            ]
        )
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(sheet_id)
        logger.info(f"Подключено к таблице: {sheet.title}")

        for name in ["GIM", "TR"]:
            try:
                sheet.worksheet(name)
            except WorksheetNotFound:
                sheet.add_worksheet(title=name, rows=100, cols=20)
                logger.info(f"Создан новый лист: {name}")

        return sheet
    except Exception as e:
        logger.error(f"Ошибка Google Sheets: {e}")
        return None

# ===== Команды бота =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот активен. Используйте /help для списка команд.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start — запуск\n/help — помощь")

# ===== Главная асинхронная функция =====
async def async_main():
    if not check_environment():
        return
    sheet = init_google_sheets()
    if not sheet:
        return

    port = int(os.environ.get("PORT", 10000))
    await start_health_server(port)

    application = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    await application.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=os.environ["WEBHOOK_URL"],
        drop_pending_updates=True
    )

# ===== Запуск =====
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(async_main())
