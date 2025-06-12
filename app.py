import os
import logging
import json
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

# Настройки
TOKEN = os.getenv("7712104265:AAEatKHUM-MHrp2YRzFFuMf9d282ormf0Cs")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "hesabla")
CREDS_FILE = os.getenv("CREDS_FILE", "gspread_key.json")

# Константы состояний
CHOOSE_MODE, CHOOSE_TYPE, ENTER_DATE, ENTER_NAME, ENTER_WORK_TYPE, ENTER_BT, ENTER_CARD, ENTER_HELPER, ENTER_EARNED, ENTER_OT, ENTER_DINCEL = range(11)

# Данные пользователя
user_data_dict = {}

# Инициализация Google Sheets
def init_sheet(sheet_type="TR"):
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME)
    return sheet.worksheet(sheet_type)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Привет! Напиши GIM или TR, чтобы выбрать режим.")
    return CHOOSE_MODE

async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    mode = update.message.text.strip().upper()
    if mode not in ["GIM", "TR"]:
        await update.message.reply_text("Пожалуйста, напиши GIM или TR.")
        return CHOOSE_MODE
    user_data_dict[update.effective_user.id] = {"mode": mode}
    await update.message.reply_text("Пожалуйста, напиши WORK или OUT.")
    return CHOOSE_TYPE

async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    mode = user_data_dict.get(update.effective_user.id, {}).get("mode", "")
    type_ = update.message.text.strip().upper()
    user_data_dict[update.effective_user.id]["type"] = type_

    await update.message.reply_text("Введите дату:")
    return ENTER_DATE

async def enter_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_dict[update.effective_user.id]["date"] = update.message.text
    await update.message.reply_text("Введите имя:")
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_dict[update.effective_user.id]["name"] = update.message.text
    await update.message.reply_text("Введите work type:")
    return ENTER_WORK_TYPE

async def enter_work_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_dict[update.effective_user.id]["work_type"] = update.message.text
    await update.message.reply_text("Введите BT:")
    return ENTER_BT

async def enter_bt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_dict[update.effective_user.id]["bt"] = update.message.text
    await update.message.reply_text("Введите имя:")
    return ENTER_CARD

async def enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_dict[update.effective_user.id]["card"] = update.message.text
    await update.message.reply_text("Введите helper name:")
    return ENTER_HELPER

async def enter_helper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_dict[update.effective_user.id]["helper"] = update.message.text
    await update.message.reply_text("Введите what they earned:")
    return ENTER_EARNED

async def enter_earned(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_dict[update.effective_user.id]["earned"] = update.message.text
    await update.message.reply_text("Введите ot:")
    return ENTER_OT

async def enter_ot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_dict[update.effective_user.id]["ot"] = update.message.text
    await update.message.reply_text("Введите work type:")
    return ENTER_DINCEL

async def enter_dincel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_dict[update.effective_user.id]["dincel"] = update.message.text

    data = user_data_dict.pop(update.effective_user.id, {})
    sheet = init_sheet("GIM" if data["mode"] == "GIM" else "TR")

    row = [
        data.get("date"), data.get("name"), data.get("work_type"),
        data.get("bt"), data.get("card"), data.get("helper"),
        data.get("earned"), data.get("ot"), data.get("dincel")
    ]
    sheet.append_row(row)
    await update.message.reply_text("Данные успешно записаны.")
    return ConversationHandler.END

def main():
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
            ENTER_HELPER: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_helper)],
            ENTER_EARNED: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_earned)],
            ENTER_OT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_ot)],
            ENTER_DINCEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_dincel)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
