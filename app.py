import os
import json
import gspread
from telegram import Update
from telegram.error import RetryAfter
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from google.oauth2.service_account import Credentials
from datetime import datetime
import asyncio
import logging

# === Настройка логгирования ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Переменные окружения ===
TOKEN = os.environ.get("BOT_TOKEN")
CREDS_FILE = os.environ.get("CREDS_FILE")
SPREADSHEET_NAME = os.environ.get("SHEET_NAME")

# === Google Sheets Setup ===
with open(CREDS_FILE) as f:
    data = json.load(f)
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(data, scopes=scopes)
client = gspread.authorize(credentials)
sheet = client.open(SPREADSHEET_NAME)

# === Состояния ===
CHOOSE_MODE, ENTER_DATE, ENTER_NAME, ENTER_WORK_TYPE, ENTER_BT, ENTER_CARD, ENTER_HELPER_NAME, ENTER_EARNED, ENTER_OT, ENTER_DINCEL, ENTER_TIME = range(11)

# === Безопасная отправка сообщений с обработкой Flood Control ===
async def safe_reply_text(update: Update, text: str, max_retries=3):
    for attempt in range(max_retries):
        try:
            await update.message.reply_text(text)
            return True
        except RetryAfter as e:
            wait_time = e.retry_after + 0.5
            logger.warning(f"Flood control exceeded. Waiting {wait_time} seconds...")
            await asyncio.sleep(wait_time)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    return False

# === Модифицированные обработчики с безопасной отправкой ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply_text(update, "Выберите режим: GIM или TR.")
    return CHOOSE_MODE

async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = update.message.text.strip().upper()
    context.user_data["mode"] = mode
    if mode == "GIM":
        await safe_reply_text(update, "Введите дату (например: 12.06)")
        return ENTER_DATE
    elif mode == "TR":
        await safe_reply_text(update, "Введите тип TR (WORK или OUT)")
        return ENTER_WORK_TYPE
    else:
        await safe_reply_text(update, "Неверный режим. Напишите GIM или TR.")
        return CHOOSE_MODE

# ... (остальные обработчики аналогично модифицировать с использованием safe_reply_text)

async def enter_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["time"] = update.message.text
    user_data = context.user_data
    now = datetime.now().strftime("%-d-%b")

    try:
        if user_data["mode"] == "GIM":
            row = [
                now, user_data["name"], user_data["work_type"], user_data["bt"],
                "", "", user_data["card"], "", "", "", user_data["helper_name"],
                user_data["earned"], "", "", "", "", user_data["time"]
            ]
            sheet.worksheet("GIM").append_row(row, value_input_option="USER_ENTERED")

        elif user_data["mode"] == "TR":
            if user_data["work_type"].upper() == "WORK":
                row = [
                    now, user_data["name"], user_data["work_type"], user_data["bt"],
                    "", "", user_data["card"], "", "", "", user_data["helper_name"],
                    user_data["earned"], "", "", "", "", user_data["time"]
                ]
                sheet.worksheet("TR").append_row(row, value_input_option="USER_ENTERED")
            elif user_data["work_type"].upper() == "OUT":
                row = [""] * 18 + [user_data["earned"], user_data["time"]]
                sheet.worksheet("TR").append_row(row, value_input_option="USER_ENTERED")

        await safe_reply_text(update, "Данные сохранены.")
    except Exception as e:
        logger.error(f"Error saving to Google Sheets: {e}")
        await safe_reply_text(update, "Ошибка при сохранении данных. Попробуйте позже.")
    
    return ConversationHandler.END

# === Основная функция запуска ===
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_mode)],
            ENTER_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_date)],
            ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
            ENTER_WORK_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_work_type)],
            ENTER_BT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_bt)],
            ENTER_CARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_card)],
            ENTER_HELPER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_helper_name)],
            ENTER_EARNED: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_earned)],
            ENTER_OT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_ot)],
            ENTER_DINCEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_dincel)],
            ENTER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_time)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    # На Render лучше использовать polling, а не webhook
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # Бесконечный цикл
    while True:
        await asyncio.sleep(3600)  # Спим 1 час

    await app.updater.stop()
    await app.stop()
    await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
