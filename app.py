import os
import json
import gspread
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from google.oauth2.service_account import Credentials
from datetime import datetime

# === Переменные окружения ===
TOKEN = os.environ.get("BOT_TOKEN")
CREDS_FILE = os.environ.get("CREDS_FILE")
SPREADSHEET_NAME = os.environ.get("SHEET_NAME")

# === Google Sheets Setup ===
with open(CREDS_FILE) as source:
    info = json.load(source)

scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(info, scopes=scopes)
client = gspread.authorize(credentials)
sheet = client.open(SPREADSHEET_NAME)

# === Состояния ===
CHOOSE_MODE, ENTER_DATE, ENTER_NAME, ENTER_WORK_TYPE, ENTER_BT, ENTER_CARD, ENTER_HELPER_NAME, ENTER_EARNED, ENTER_OT, ENTER_DINCEL, ENTER_TIME = range(11)

# === Обработчики ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите режим: GIM или TR.")
    return CHOOSE_MODE

async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = update.message.text.strip().upper()
    context.user_data["mode"] = mode
    if mode == "GIM":
        await update.message.reply_text("Введите дату (например: 12.06)")
        return ENTER_DATE
    elif mode == "TR":
        await update.message.reply_text("Введите тип TR (WORK или OUT)")
        return ENTER_WORK_TYPE
    else:
        await update.message.reply_text("Неверный режим. Напишите GIM или TR.")
        return CHOOSE_MODE

async def enter_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["date"] = update.message.text
    await update.message.reply_text("Введите имя")
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Введите тип работы")
    return ENTER_WORK_TYPE

async def enter_work_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["work_type"] = update.message.text
    await update.message.reply_text("Введите BT")
    return ENTER_BT

async def enter_bt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["bt"] = update.message.text
    await update.message.reply_text("Введите карту")
    return ENTER_CARD

async def enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["card"] = update.message.text
    await update.message.reply_text("Введите имя помощника")
    return ENTER_HELPER_NAME

async def enter_helper_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["helper_name"] = update.message.text
    await update.message.reply_text("Введите сумму заработка")
    return ENTER_EARNED

async def enter_earned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["earned"] = update.message.text
    await update.message.reply_text("Введите OT")
    return ENTER_OT

async def enter_ot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ot"] = update.message.text
    await update.message.reply_text("Введите DINCEL")
    return ENTER_DINCEL

async def enter_dincel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["dincel"] = update.message.text
    await update.message.reply_text("Введите время")
    return ENTER_TIME

async def enter_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["time"] = update.message.text

    user_data = context.user_data
    now = datetime.now().strftime("%-d-%b")

    if user_data["mode"] == "GIM":
        row = [
            now,
            user_data["name"],
            user_data["work_type"],
            user_data["bt"],
            "", "",  # пропуск TR и AT
            user_data["card"],
            "", "", "",  # пропуск equipment, maintenance, gas
            user_data["helper_name"],
            user_data["earned"],
            "", "", "", "",  # пропуск Gross → bonus
            user_data["time"],
        ]
        sheet.worksheet("GIM").append_row(row, value_input_option="USER_ENTERED")

    elif user_data["mode"] == "TR":
        if user_data["work_type"].upper() == "WORK":
            row = [
                now,
                user_data["name"],
                user_data["work_type"],
                user_data["bt"],
                "", "",  # пропуск TR и AT
                user_data["card"],
                "", "", "",  # пропуск equipment, maintenance, gas
                user_data["helper_name"],
                user_data["earned"],
                "", "", "", "",  # пропуск Gross → bonus
                user_data["time"],
            ]
            sheet.worksheet("TR").append_row(row, value_input_option="USER_ENTERED")

        elif user_data["work_type"].upper() == "OUT":
            row = [
                "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",  # пропуск
                user_data["earned"],
                user_data["time"]
            ]
            sheet.worksheet("TR").append_row(row, value_input_option="USER_ENTERED")

    await update.message.reply_text("Данные сохранены.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

# === Запуск бота ===
def main():
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

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url="https://telegram-finance-bot-0ify.onrender.com"
    )

if __name__ == "__main__":
    main()
