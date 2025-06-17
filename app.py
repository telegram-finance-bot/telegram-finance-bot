import os
import json
import gspread
from datetime import datetime
import logging
from flask import Flask
from threading import Thread

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from google.oauth2.service_account import Credentials
from gspread.exceptions import SpreadsheetNotFound

# === Flask для Render пинга ===
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running!", 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=8000)

# === Логгинг ===
logging.basicConfig(level=logging.INFO)

# === Переменные окружения ===
TOKEN = os.environ["BOT_TOKEN"]
SHEET_NAME = os.environ["SHEET_NAME"]
CREDS_FILE = os.environ["CREDS_FILE"]

# === Google Sheets ===
with open(CREDS_FILE) as f:
    creds_data = json.load(f)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
client = gspread.authorize(credentials)
try:
    sheet = client.open(SHEET_NAME)
except SpreadsheetNotFound:
    logging.error("Google Sheet не найден. Проверь имя таблицы и доступ.")
    exit(1)

# === Состояния ===
CHOOSE_MODE, ENTER_DATE, ENTER_NAME, ENTER_TYPE, ENTER_BT, ENTER_CARD, ENTER_HELPER, ENTER_EARNED, ENTER_OT, ENTER_DINCEL, ENTER_TIME = range(11)

# === Хендлеры ===
aimport logging  # убедись, что это есть вверху

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("▶️ Получена команда /start")
    await update.message.reply_text("Выберите режим: GIM или TR.")
    return CHOOSE_MODE

async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = update.message.text.strip().upper()
    if mode not in ["GIM", "TR"]:
        await update.message.reply_text("Пожалуйста, выбери GIM или TR.")
        return CHOOSE_MODE
    context.user_data["mode"] = mode
    if mode == "GIM":
        await update.message.reply_text("Введите дату (ДД.ММ):")
        return ENTER_DATE
    else:
        await update.message.reply_text("Введите тип TR: WORK или OUT")
        return ENTER_TYPE

async def enter_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["date"] = update.message.text
    await update.message.reply_text("Имя:")
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Тип работы:")
    return ENTER_TYPE

async def enter_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["work_type"] = update.message.text
    if context.user_data["mode"] == "TR" and context.user_data["work_type"].upper() == "OUT":
        await update.message.reply_text("Введите сумму (earned):")
        return ENTER_EARNED
    await update.message.reply_text("Введите BT:")
    return ENTER_BT

async def enter_bt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["bt"] = update.message.text
    await update.message.reply_text("Карта:")
    return ENTER_CARD

async def enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["card"] = update.message.text
    await update.message.reply_text("Имя помощника:")
    return ENTER_HELPER

async def enter_helper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["helper"] = update.message.text
    await update.message.reply_text("Сумма (earned):")
    return ENTER_EARNED

async def enter_earned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["earned"] = update.message.text
    if context.user_data["mode"] == "TR" and context.user_data["work_type"].upper() == "OUT":
        await update.message.reply_text("Время:")
        return ENTER_TIME
    await update.message.reply_text("OT:")
    return ENTER_OT

async def enter_ot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ot"] = update.message.text
    await update.message.reply_text("DINCEL:")
    return ENTER_DINCEL

async def enter_dincel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["dincel"] = update.message.text
    await update.message.reply_text("Время:")
    return ENTER_TIME

async def enter_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["time"] = update.message.text
    user = context.user_data
    now = datetime.now().strftime("%-d-%b")

    if user["mode"] == "GIM":
        row = [now, user["name"], user["work_type"], user["bt"], "", "", user["card"], "", "", "", user["helper"], user["earned"], "", "", "", "", user["time"]]
        sheet.worksheet("GIM").append_row(row, value_input_option="USER_ENTERED")
    elif user["mode"] == "TR":
        if user["work_type"].upper() == "WORK":
            row = [now, user["name"], user["work_type"], user["bt"], "", "", user["card"], "", "", "", user["helper"], user["earned"], "", "", "", "", user["time"]]
            sheet.worksheet("TR").append_row(row, value_input_option="USER_ENTERED")
        else:
            row = [""] * 18 + [user["earned"], user["time"]]
            sheet.worksheet("TR").append_row(row, value_input_option="USER_ENTERED")

    await update.message.reply_text("✅ Данные сохранены.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

# === Запуск Telegram + Flask ===
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
    await app.bot.set_webhook("https://telegram-finance-bot-0ify.onrender.com")
    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url="https://telegram-finance-bot-0ify.onrender.com"
    )

if __name__ == "__main__":
    from nest_asyncio import apply
    apply()
    Thread(target=run_flask).start()
    import asyncio
    try:
        asyncio.run(main())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
