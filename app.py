import os
import json
import logging
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

# Получение переменных окружения
TOKEN = os.getenv("TOKEN")
SPREADSHEET_NAME = os.getenv("SHEET_NAME", "hesabla")
CREDS_FILE = os.getenv("CREDS_FILE", "gspread_key.json")

# Состояния
CHOOSE_MODE, CHOOSE_TYPE = range(2)
ENTER_DATE, ENTER_NAME, ENTER_WORK_TYPE, ENTER_BT, ENTER_CARD, ENTER_HELPER_NAME, ENTER_HELPER_EARNED, ENTER_OT, ENTER_DINCEL, ENTER_TIME = range(10)

user_data_dict = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши GIM или TR, чтобы выбрать режим.")
    return CHOOSE_MODE

async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip().upper()
    chat_id = update.message.chat_id

    if user_input == "GIM":
        user_data_dict[chat_id] = {"mode": "GIM"}
        await update.message.reply_text("Введите дату:")
        return ENTER_DATE
    elif user_input == "TR":
        await update.message.reply_text("Пожалуйста, напиши WORK или OUT.")
        return CHOOSE_TYPE
    else:
        await update.message.reply_text("Пожалуйста, введите GIM или TR.")
        return CHOOSE_MODE

async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text.strip().upper()
    if text in ["WORK", "OUT"]:
        user_data_dict[chat_id] = {"mode": "TR", "type": text}
        await update.message.reply_text("Введите дату:")
        return ENTER_DATE
    else:
        await update.message.reply_text("Пожалуйста, напиши WORK или OUT.")
        return CHOOSE_TYPE

async def collect_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text.strip()
    user_data = user_data_dict.get(chat_id, {})

    fields_gim = ["date", "name", "work_type", "BT", "T", "AT", "card", "helper_name", "what_they_earned"]
    fields_work = ["date", "name", "work_type", "BT", "card", "helper_name", "what_they_earned", "ot", "dincel", "time"]
    fields_out = ["date", "name", "work_type", "BT", "card", "helper_name", "what_they_earned", "ot", "dincel"]

    current_field = user_data.get("current_field")
    if not current_field:
        if user_data.get("mode") == "GIM":
            user_data["fields"] = fields_gim
        elif user_data.get("type") == "WORK":
            user_data["fields"] = fields_work
        else:
            user_data["fields"] = fields_out
        user_data["current_field_index"] = 0
        current_field = user_data["fields"][0]
        user_data["current_field"] = current_field

    user_data[current_field] = text
    user_data["current_field_index"] += 1

    if user_data["current_field_index"] < len(user_data["fields"]):
        next_field = user_data["fields"][user_data["current_field_index"]]
        user_data["current_field"] = next_field
        await update.message.reply_text(f"Введите {next_field.replace('_', ' ')}:")
        return ENTER_DATE
    else:
        write_to_sheet(user_data)
        await update.message.reply_text("Данные успешно записаны.")
        user_data_dict.pop(chat_id, None)
        return ConversationHandler.END

def write_to_sheet(user_data):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).worksheet("TR")

    values = [user_data.get(field, "") for field in user_data.get("fields", [])]
    sheet.append_row(values, value_input_option="USER_ENTERED")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_mode)],
            CHOOSE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_type)],
            ENTER_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_input)],
        },
        fallbacks=[]
    )

    application.add_handler(conv_handler)
    application.run_polling()
