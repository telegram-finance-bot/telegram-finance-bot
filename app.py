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
from gspread.exceptions import SpreadsheetNotFound, APIError
from threading import Thread

# === Логгирование ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Переменные среды ===
TOKEN = os.environ.get("BOT_TOKEN")
SHEET_NAME = os.environ.get("SHEET_NAME")
CREDS_FILE = os.environ.get("CREDS_FILE")

if not all([TOKEN, SHEET_NAME, CREDS_FILE]):
    logger.error("Не хватает обязательных переменных окружения!")
    exit(1)

# === Google Sheets ===
try:
    with open(CREDS_FILE) as f:
        creds_data = json.load(f)

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file"
    ]
    credentials = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
    client = gspread.authorize(credentials)
    sheet = client.open(SHEET_NAME)
    
    # Проверка и создание необходимых листов
    for worksheet_name in ['GIM', 'TR']:
        try:
            sheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            sheet.add_worksheet(title=worksheet_name, rows=100, cols=20)
            logger.info(f"Создан новый лист: {worksheet_name}")
            
except SpreadsheetNotFound:
    logger.error("Google Sheet не найден. Проверь имя и доступ.")
    exit(1)
except Exception as e:
    logger.error(f"Ошибка инициализации Google Sheets: {e}")
    exit(1)

# === Состояния ===
(
    CHOOSE_MODE, ENTER_DATE, ENTER_NAME, ENTER_TYPE, 
    ENTER_BT, ENTER_CARD, ENTER_HELPER, 
    ENTER_EARNED, ENTER_OT, ENTER_DINCEL, ENTER_TIME
) = range(11)

# === Хендлеры ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Новый пользователь: {update.effective_user.id}")
    await update.message.reply_text(
        "🏋️‍♂️ Бот для учета тренировок\n\n"
        "Выберите режим:\n"
        "• <b>GIM</b> - для работы в зале\n"
        "• <b>TR</b> - для тренировок",
        parse_mode='HTML'
    )
    return CHOOSE_MODE

async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = update.message.text.strip().upper()
    if mode not in ["GIM", "TR"]:
        await update.message.reply_text("⚠️ Пожалуйста, выбери GIM или TR.")
        return CHOOSE_MODE
        
    context.user_data.clear()
    context.user_data["mode"] = mode
    reply = "📅 Введите дату (ДД.ММ):" if mode == "GIM" else "Введите тип TR: WORK или OUT"
    await update.message.reply_text(reply)
    return ENTER_DATE if mode == "GIM" else ENTER_TYPE

# ... [остальные обработчики остаются аналогичными, но добавьте обработку ошибок] ...

async def enter_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["time"] = update.message.text
    user = context.user_data
    now = datetime.now().strftime("%d-%b")

    try:
        worksheet = sheet.worksheet(user["mode"])
        
        if user["mode"] == "GIM":
            row = [
                now, user["name"], user["work_type"], user["bt"],
                "", "", user["card"], "", "", "", user["helper"],
                user["earned"], "", "", "", "", user["time"]
            ]
        elif user["work_type"].upper() == "WORK":
            row = [
                now, user["name"], user["work_type"], user["bt"],
                "", "", user["card"], "", "", "", user["helper"],
                user["earned"], "", "", "", "", user["time"]
            ]
        else:
            row = [""] * 18 + [user["earned"], user["time"]]
            
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        await update.message.reply_text("✅ Данные успешно сохранены!")
        
    except APIError as e:
        logger.error(f"Ошибка Google Sheets: {e}")
        await update.message.reply_text("❌ Ошибка при сохранении данных")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        await update.message.reply_text("❌ Произошла ошибка")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Операция отменена")
    return ConversationHandler.END

# === Webhook управление ===
async def safe_set_webhook(app, url, max_retries=3):
    for attempt in range(max_retries):
        try:
            await app.bot.set_webhook(url)
            logger.info("Webhook успешно установлен")
            return True
        except RetryAfter as e:
            wait = e.retry_after + 2
            logger.warning(f"Flood control, ждем {wait} секунд...")
            await asyncio.sleep(wait)
        except Exception as e:
            logger.error(f"Ошибка установки webhook: {e}")
    return False

# === Основной запуск ===
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_mode)],
            ENTER_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_date)],
            ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
            ENTER_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_type)],
            ENTER_BT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_bt)],
            ENTER_CARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_card)],
            ENTER_HELPER: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_helper)],
            ENTER_EARNED: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_earned)],
            ENTER_OT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_ot)],
            ENTER_DINCEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_dincel)],
            ENTER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_time)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    webhook_url = "https://telegram-finance-bot-0ify.onrender.com"
    if not await safe_set_webhook(app, webhook_url):
        logger.error("Не удалось установить webhook")
        exit(1)
        
    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=webhook_url,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}")
