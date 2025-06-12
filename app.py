import os
import json
import logging
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Настройки
TOKEN = os.getenv("TOKEN")
SPREADSHEET_NAME = os.getenv("SHEET_NAME", "hesabla")
CREDS_FILE = os.getenv("CREDS_FILE", "gspread_key.json")

# Константы состояний
(
    CHOOSE_MODE,
    CHOOSE_TYPE,
    ENTER_DATE,
    ENTER_NAME,
    ENTER_WORK_TYPE,
    ENTER_BT,
    ENTER_CARD,
    ENTER_HELPER_NAME,
    ENTER_EARNED,
) = range(9)

# Данные пользователя
user_data_dict = {}

# Инициализация Google Sheets
def init_sheet(sheet_type="TR"):
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME)
    return sheet.worksheet(sheet_type)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Привет! Напиши GIM или TR, чтобы выбрать режим.")
    return CHOOSE_MODE

async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.upper()
    user_data_dict[update.effective_chat.id] = {"mode": text}
    await update.message.reply_text("Пожалуйста, напиши WORK или OUT.")
    return CHOOSE_TYPE

async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.upper()
    user_data = user_data_dict[update.effective_chat.id]
    user_data["type"] = text

    await update.message.reply_text("Введите дату:")
    return ENTER_DATE

async def enter_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_dict[update.effective_chat.id]["date"] = update.message.text
    await update.message.reply_text("Введите имя:")
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_dict[update.effective_chat.id]["name"] = update.message.text
    await update.message.reply_text("Введите work type:")
    return ENTER_WORK_TYPE

async def enter_work_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_dict[update.effective_chat.id]["work_type"] = update.message.text
    await update.message.reply_text("Введите BT:")
    return ENTER_BT

async def enter_bt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_dict[update.effective_chat.id]["bt"] = update.message.text
    await update.message.reply_text("Введите card:")
    return ENTER_CARD

async def enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_dict[update.effective_chat.id]["card"] = update.message.text
    await update.message.reply_text("Введите helper name:")
    return ENTER_HELPER_NAME

async def enter_helper_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_dict[update.effective_chat.id]["helper_name"] = update.message.text
    await update.message.reply_text("Введите what they earned:")
    return ENTER_EARNED

async def enter_earned(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_dict[update.effective_chat.id]["earned"] = update.message.text
    await save_data(update, context)
    return ConversationHandler.END

async def save_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data = user_data_dict.get(chat_id, {})
    mode = user_data.get("mode", "TR")
    sheet = init_sheet(mode)

    row = [
        user_data.get("date", ""),
        user_data.get("name", ""),
        user_data.get("work_type", ""),
        user_data.get("bt", ""),
        user_data.get("card", ""),
        user_data.get("helper_name", ""),
        user_data.get("earned", ""),
    ]
    sheet.append_row(row)
    await update.message.reply_text("Данные успешно записаны.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_mode)],
            CHOOSE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_type)],
            ENTER_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_date)],
            ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
            ENTER_WORK_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_work_type)],
            ENTER_BT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_bt)],
            ENTER_CARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_card)],
            ENTER_HELPER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_helper_name)],
            ENTER_EARNED: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_earned)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.run_polling()
