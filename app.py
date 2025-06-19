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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Переменные среды ===
TOKEN = os.environ.get("BOT_TOKEN")
SHEET_ID = os.environ.get("SHEET_ID")
CREDS_FILE = os.environ.get("CREDS_FILE")

if not all([TOKEN, SHEET_ID, CREDS_FILE]):
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
    sheet = client.open_by_key(SHEET_ID)

    for name in ['GIM', 'TR']:
        try:
            sheet.worksheet(name)
        except gspread.WorksheetNotFound:
            sheet.add_worksheet(title=name, rows=100, cols=20)
except SpreadsheetNotFound:
    logger.error("Google Sheet не найден. Проверь ID и доступ.")
    exit(1)
except Exception as e:
    logger.error(f"Ошибка инициализации Google Sheets: {e}")
    exit(1)

# === Состояния ===
(
    CHOOSE_MODE, ENTER_DATE, ENTER_NAME, ENTER_TYPE,
    ENTER_BT, ENTER_CARD, ENTER_HELPER,
    ENTER_EARNED, ENTER_TIME
) = range(9)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏋️‍♂️ Бот для учета тренировок\n\n"
        "Выберите режим:\n"
        "• GIM — зал\n"
        "• TR — тренировка"
    )
    return CHOOSE_MODE

async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = update.message.text.strip().upper()
    if mode not in ["GIM", "TR"]:
        await update.message.reply_text("Выберите GIM или TR")
        return CHOOSE_MODE
    context.user_data.clear()
    context.user_data["mode"] = mode
    await update.message.reply_text("📅 Введите дату (ДД.ММ):")
    return ENTER_DATE

async def enter_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["date"] = update.message.text.strip()
    await update.message.reply_text("👤 Введите имя:")
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("🏷️ Введите тип: WORK или OUT")
    return ENTER_TYPE

async def enter_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    work_type = update.message.text.strip().upper()
    if work_type not in ["WORK", "OUT"]:
        await update.message.reply_text("Введите WORK или OUT")
        return ENTER_TYPE
    context.user_data["work_type"] = work_type
    await update.message.reply_text("🔢 Введите BT:")
    return ENTER_BT

async def enter_bt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["bt"] = update.message.text.strip()
    await update.message.reply_text("💳 Введите карту:")
    return ENTER_CARD

async def enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["card"] = update.message.text.strip()
    await update.message.reply_text("👥 Введите помощника:")
    return ENTER_HELPER

async def enter_helper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["helper"] = update.message.text.strip()
    await update.message.reply_text("💰 Введите сумму:")
    return ENTER_EARNED

async def enter_earned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["earned"] = update.message.text.strip()
    await update.message.reply_text("⏰ Введите время:")
    return ENTER_TIME

async def enter_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["time"] = update.message.text.strip()
    data = context.user_data
    try:
        worksheet = sheet.worksheet(data["mode"])
        row = [
            data["date"], data["name"], data["work_type"], data["bt"],
            data["card"], data["helper"], data["earned"], data["time"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        await update.message.reply_text("✅ Сохранено!")
    except Exception as e:
        logger.error(f"Ошибка при сохранении: {e}")
        await update.message.reply_text("❌ Ошибка при сохранении")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Отменено")
    return ConversationHandler.END

async def safe_set_webhook(app, url, max_retries=3):
    for _ in range(max_retries):
        try:
            await app.bot.set_webhook(url)
            return True
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
    return False

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    conv = ConversationHandler(
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
            ENTER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_time)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)

    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
    if not await safe_set_webhook(app, WEBHOOK_URL):
        logger.error("Не удалось установить webhook")
        exit(1)

    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    asyncio.run(main())
