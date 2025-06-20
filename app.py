import os
import json
import gspread
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler
)
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound
from datetime import datetime

# ===== Настройки =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы для ConversationHandler
TR_TYPE, WORK_DATA, OUT_DATA = range(3)

# ===== Инициализация Google Sheets =====
def init_google_sheets():
    try:
        creds = Credentials.from_service_account_file(
            os.environ['CREDS_FILE'],
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(os.environ['SHEET_ID'])
        
        # Создаем листы если их нет
        for sheet_name in ['GIM', 'TR']:
            try:
                sheet.worksheet(sheet_name)
            except WorksheetNotFound:
                sheet.add_worksheet(title=sheet_name, rows=100, cols=20)
        
        return sheet
    except Exception as e:
        logger.error(f"Google Sheets error: {e}")
        return None

# ===== Обработчики команд =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать! Выберите режим:\n"
        "/gim - Режим GIM\n"
        "/tr - Режим TR"
    )

async def gim_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sheet = init_google_sheets()
    if not sheet:
        await update.message.reply_text("Ошибка подключения к Google Sheets")
        return
    
    worksheet = sheet.worksheet('GIM')
    data = [str(datetime.now()), update.message.from_user.full_name, "GIM запись"]
    worksheet.append_row(data)
    
    await update.message.reply_text("Данные записаны в лист GIM")

async def tr_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Выбран режим TR. Выберите тип:\n"
        "/work - Работа\n"
        "/out - Выход"
    )
    return TR_TYPE

async def tr_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите данные для WORK (через запятую):\nДата, Имя, Проект, Часы")
    return WORK_DATA

async def tr_out(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите данные для OUT (через запятую):\nДата, Имя, Причина")
    return OUT_DATA

async def process_work_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sheet = init_google_sheets()
    if not sheet:
        await update.message.reply_text("Ошибка подключения к Google Sheets")
        return ConversationHandler.END
    
    try:
        data = update.message.text.split(',')
        worksheet = sheet.worksheet('TR')
        worksheet.append_row(['WORK'] + [item.strip() for item in data])
        await update.message.reply_text("Данные WORK успешно записаны")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")
    
    return ConversationHandler.END

async def process_out_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sheet = init_google_sheets()
    if not sheet:
        await update.message.reply_text("Ошибка подключения к Google Sheets")
        return ConversationHandler.END
    
    try:
        data = update.message.text.split(',')
        worksheet = sheet.worksheet('TR')
        worksheet.append_row(['OUT'] + [item.strip() for item in data])
        await update.message.reply_text("Данные OUT успешно записаны")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена")
    return ConversationHandler.END

# ===== Главная функция =====
def main():
    # Проверка переменных окружения
    required_vars = ['BOT_TOKEN', 'SHEET_ID', 'CREDS_FILE', 'WEBHOOK_URL', 'PORT']
    if any(os.environ.get(var) is None for var in required_vars):
        raise RuntimeError("Не все переменные окружения установлены")

    # Настройка обработчиков
    application = ApplicationBuilder().token(os.environ['BOT_TOKEN']).build()

    # Обработчик для режима TR с разными состояниями
    tr_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('tr', tr_mode)],
        states={
            TR_TYPE: [
                CommandHandler('work', tr_work),
                CommandHandler('out', tr_out)
            ],
            WORK_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_work_data)],
            OUT_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_out_data)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('gim', gim_mode))
    application.add_handler(tr_conv_handler)

    # Запуск вебхука
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ['PORT']),
        webhook_url=os.environ['WEBHOOK_URL'],
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
