import os
import json
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Настройки
TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_NAME = os.getenv("SHEET_NAME", "hesabla")
CREDS_FILE = os.getenv("CREDS_FILE", "gspread_key.json")
WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/webhook"

# Константы состояний
(
    CHOOSE_MODE, CHOOSE_TYPE, ENTER_DATE, ENTER_NAME, ENTER_WORK_TYPE,
    ENTER_BT, ENTER_CARD, ENTER_HELPER_NAME, ENTER_EARNED,
    ENTER_OT, ENTER_DINCEL, ENTER_TIME
) = range(12)

# Данные пользователя
user_data_dict = {}

# Google Sheets
def init_sheet(sheet_name):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open(SPREADSHEET_NAME)
    return spreadsheet.worksheet(sheet_name)

def save_data_to_sheet(sheet, data):
    sheet.append_row(data)

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши GIM или TR, чтобы выбрать режим.")
    return CHOOSE_MODE

async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = update.message.text.upper()
    user_data_dict[update.effective_chat.id] = {'mode': mode}
    await update.message.reply_text("Введите дату:")
    return ENTER_DATE

async def enter_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_chat.id]['date'] = update.message.text
    await update.message.reply_text("Введите имя:")
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_chat.id]['name'] = update.message.text
    await update.message.reply_text("Введите work type:")
    return ENTER_WORK_TYPE

async def enter_work_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_chat.id]['work_type'] = update.message.text
    await update.message.reply_text("Введите BT:")
    return ENTER_BT

async def enter_bt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_chat.id]['bt'] = update.message.text
    await update.message.reply_text("Введите card:")
    return ENTER_CARD

async def enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_chat.id]['card'] = update.message.text
    await update.message.reply_text("Введите helper name:")
    return ENTER_HELPER_NAME

async def enter_helper_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_chat.id]['helper_name'] = update.message.text
    await update.message.reply_text("Введите what they earned:")
    return ENTER_EARNED

async def enter_earned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_chat.id]['earned'] = update.message.text
    await update.message.reply_text("Введите ot:")
    return ENTER_OT

async def enter_ot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_chat.id]['ot'] = update.message.text
    await update.message.reply_text("Введите dincel:")
    return ENTER_DINCEL

async def enter_dincel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_chat.id]['dincel'] = update.message.text
    await update.message.reply_text("Введите время:")
    return ENTER_TIME

async def enter_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict[update.effective_chat.id]['time'] = update.message.text

    user_data = user_data_dict[update.effective_chat.id]
    sheet = init_sheet(user_data['mode'])
    row = [
        user_data.get('date', ''),
        user_data.get('name', ''),
        user_data.get('work_type', ''),
        user_data.get('bt', ''),
        '',
        '',
        user_data.get('card', ''),
        user_data.get('helper_name', ''),
        user_data.get('earned', ''),
        '',
        '',
        '',
        user_data.get('time', '')
    ]
    save_data_to_sheet(sheet, row)
    await update.message.reply_text("Данные успешно записаны.")
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
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
        fallbacks=[]
    )

    application.add_handler(conv_handler)

    # Включение Webhook
    application.run_polling()
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL
    )

if __name__ == '__main__':
    main()
