# В начале main() добавьте:
logger.info("=== ПРОВЕРКА ПЕРЕМЕННЫХ ===")
logger.info(f"TOKEN: {'установлен' if TOKEN else 'НЕТ'}")
logger.info(f"SHEET_ID: {'установлен' if SHEET_ID else 'НЕТ'}")
logger.info(f"CREDS_FILE: {'существует' if CREDS_FILE and os.path.exists(CREDS_FILE) else 'НЕТ'}")
logger.info(f"WEBHOOK_URL: {'установлен' if WEBHOOK_URL else 'НЕТ'}")

if not TOKEN:
    logger.error("Токен бота не найден! Проверьте секрет 'telegram-bot-secret'")
if not SHEET_ID:
    logger.error("ID таблицы не найден! Проверьте секрет 'google-sheet-secret'")
if not CREDS_FILE or not os.path.exists(CREDS_FILE):
    logger.error(f"Файл учетных данных не найден по пути: {CREDS_FILE}")

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

# === Настройка логгирования ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Проверка переменных окружения ===
TOKEN = os.environ.get("BOT_TOKEN")
SHEET_ID = os.environ.get("SHEET_ID")  # Используем ID, а не название
CREDS_FILE = os.environ.get("CREDS_FILE")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

if not all([TOKEN, SHEET_ID, CREDS_FILE, WEBHOOK_URL]):
    logger.error("Не хватает обязательных переменных окружения!")
    exit(1)

# === Инициализация Google Sheets ===
try:
    logger.info(f"Пытаюсь открыть файл учетных данных: {CREDS_FILE}")
    
    with open(CREDS_FILE) as f:
        creds_data = json.load(f)
        service_account_email = creds_data['client_email']
        logger.info(f"Использую сервисный аккаунт: {service_account_email}")

    credentials = Credentials.from_service_account_info(creds_data, scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file"
    ])
    client = gspread.authorize(credentials)
    
    logger.info(f"Пытаюсь открыть таблицу с ID: {SHEET_ID}")
    sheet = client.open_by_key(SHEET_ID)  # Открываем по ID
    
    # Проверка и создание необходимых листов
    REQUIRED_SHEETS = ['GIM', 'TR']
    for sheet_name in REQUIRED_SHEETS:
        try:
            sheet.worksheet(sheet_name)
            logger.info(f"Лист '{sheet_name}' существует")
        except WorksheetNotFound:
            logger.info(f"Создаю новый лист: {sheet_name}")
            sheet.add_worksheet(title=sheet_name, rows=100, cols=20)

except SpreadsheetNotFound:
    logger.error(f"Таблица с ID '{SHEET_ID}' не найдена. Проверьте:")
    logger.error("1. Правильность ID таблицы")
    logger.error(f"2. Доступ для сервисного аккаунта: {service_account_email}")
    exit(1)
except Exception as e:
    logger.error(f"Ошибка инициализации Google Sheets: {e}")
    exit(1)

# ... [остальные обработчики из вашего кода остаются без изменений] ...

async def main():
    try:
        logger.info("=== ПРОВЕРКА ПЕРЕМЕННЫХ ===")
        logger.info(f"TOKEN: {'установлен' if TOKEN else 'НЕТ'}")
        logger.info(f"SHEET_ID: {SHEET_ID}")
        logger.info(f"CREDS_FILE: {'существует' if os.path.exists(CREDS_FILE) else 'НЕТ'}")
        logger.info(f"WEBHOOK_URL: {WEBHOOK_URL}")
        
        app = ApplicationBuilder().token(TOKEN).build()
        
        # ... [добавьте ваши обработчики команд] ...
        
        if not await safe_set_webhook(app, WEBHOOK_URL):
            logger.error("Не удалось установить webhook")
            exit(1)
            
        await app.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 10000)),
            webhook_url=WEBHOOK_URL,
            drop_pending_updates=True
        )
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
