import os
import json
import gspread
import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.error import RetryAfter
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from google.oauth2.service_account import Credentials
from gspread.exceptions import SpreadsheetNotFound, APIError, WorksheetNotFound

# ===== Инициализация логгера =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== Проверка переменных окружения =====
def check_environment():
    """Проверка наличия всех необходимых переменных"""
    logger.info("=== ПРОВЕРКА ПЕРЕМЕННЫХ ===")
    
    TOKEN = os.environ.get("BOT_TOKEN")
    SHEET_ID = os.environ.get("SHEET_ID")
    CREDS_FILE = os.environ.get("CREDS_FILE")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

    logger.info(f"TOKEN: {'установлен' if TOKEN else 'НЕТ'}")
    logger.info(f"SHEET_ID: {'установлен' if SHEET_ID else 'НЕТ'}")
    logger.info(f"CREDS_FILE: {'существует' if CREDS_FILE and os.path.exists(CREDS_FILE) else 'НЕТ'}")
    logger.info(f"WEBHOOK_URL: {'установлен' if WEBHOOK_URL else 'НЕТ'}")

    if not all([TOKEN, SHEET_ID, CREDS_FILE, WEBHOOK_URL]):
        missing = []
        if not TOKEN: missing.append("BOT_TOKEN")
        if not SHEET_ID: missing.append("SHEET_ID")
        if not CREDS_FILE: missing.append("CREDS_FILE")
        if not WEBHOOK_URL: missing.append("WEBHOOK_URL")
        logger.error(f"Отсутствуют переменные: {', '.join(missing)}")
        return False
    
    if not os.path.exists(CREDS_FILE):
        logger.error(f"Файл учетных данных не найден: {CREDS_FILE}")
        return False
    
    return True

# ===== Инициализация Google Sheets =====
def init_google_sheets():
    try:
        CREDS_FILE = os.environ.get("CREDS_FILE")
        SHEET_ID = os.environ.get("SHEET_ID")
        
        with open(CREDS_FILE) as f:
            creds_data = json.load(f)
            logger.info(f"Сервисный аккаунт: {creds_data['client_email']}")

        credentials = Credentials.from_service_account_info(creds_data, scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file"
        ])
        client = gspread.authorize(credentials)
        
        sheet = client.open_by_key(SHEET_ID)
        logger.info(f"Таблица открыта: {sheet.title}")
        
        # Создаем листы если их нет
        for sheet_name in ['GIM', 'TR']:
            try:
                sheet.worksheet(sheet_name)
            except WorksheetNotFound:
                sheet.add_worksheet(title=sheet_name, rows=100, cols=20)
                logger.info(f"Создан лист: {sheet_name}")
        
        return sheet
        
    except Exception as e:
        logger.error(f"Ошибка инициализации Google Sheets: {e}")
        return None

# ... [Ваши обработчики команд остаются без изменений] ...

async def main():
    if not check_environment():
        exit(1)
    
    sheet = init_google_sheets()
    if not sheet:
        exit(1)
    
    try:
        app = ApplicationBuilder().token(os.environ.get("BOT_TOKEN")).build()
        
        # ... [Ваши обработчики команд] ...
        
        WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
        await app.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 10000)),
            webhook_url=WEBHOOK_URL,
            drop_pending_updates=True
        )
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
