import os
import json
import gspread
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound
from datetime import datetime

# === Настройка логгера ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Константы ===
TR_TYPE, WORK_DATA, OUT_DATA = range(3)
REQUIRED_ENV_VARS = ['BOT_TOKEN', 'SHEET_ID', 'CREDS_FILE', 'WEBHOOK_URL', 'PORT']

# === Инициализация Google Sheets ===
def init_google_sheets():
    try:
        with open(os.environ["CREDS_FILE"]) as f:
            creds_data = json.load(f)

        credentials = Credentials.from_service_account_info(
            creds_data,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(os.environ["SHEET_ID"])
        
        # Создаем листы если их нет
        for sheet_name in ['GIM', 'TR']:
            try:
                sheet.worksheet(sheet_name)
            except WorksheetNotFound:
                sheet.add_worksheet(title=sheet_name, rows=100, cols=20)
                logger.info(f"Создан новый лист: {sheet_name}")
        
        return sheet
    except Exception as e:
        logger.error(f"Ошибка Google Sheets: {e}")
        return None

# === Обработчики команд ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать! Выберите режим:\n"
        "/gim - Режим GIM\n"
        "/tr - Режим TR"
    )

async def gim_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sheet = init_google_sheets()
    if not sheet:
        await update.message.reply_text("❌ Ошибка подключения к Google Sheets")
        return
    
    try:
        worksheet = sheet.worksheet('GIM')
        data = [datetime.now().isoformat(), update.message.from_user.full_name, "GIM запись"]
        worksheet.append_row(data)
        await update.message.reply_text("✅ Данные записаны в лист GIM")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def tr_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Выбран режим TR. Выберите тип:\n"
        "/work - Работа\n"
        "/out - Выход\n"
        "/cancel - Отмена"
    )
    return TR_TYPE

async def tr_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введите данные для WORK через запятую:\n"
        "Формат: Дата, Имя, Проект, Часы"
    )
    return WORK_DATA

async def tr_out(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введите данные для OUT через запятую:\n"
        "Формат: Дата, Имя, Причина"
    )
    return OUT_DATA

async def process_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sheet = init_google_sheets()
    if not sheet:
        await update.message.reply_text("❌ Ошибка подключения к Google Sheets")
        return ConversationHandler.END
    
    try:
        data = ['WORK'] + [item.strip() for item in update.message.text.split(',')]
        sheet.worksheet('TR').append_row(data)
        await update.message.reply_text("✅ Данные WORK успешно записаны")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
    
    return ConversationHandler.END

async def process_out(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sheet = init_google_sheets()
    if not sheet:
        await update.message.reply_text("❌ Ошибка подключения к Google Sheets")
        return ConversationHandler.END
    
    try:
        data = ['OUT'] + [item.strip() for item in update.message.text.split(',')]
        sheet.worksheet('TR').append_row(data)
        await update.message.reply_text("✅ Данные OUT успешно записаны")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Операция отменена")
    return ConversationHandler.END

# === Главная функция ===
def main():
    # Проверка переменных окружения
    for var in REQUIRED_ENV_VARS:
        if not os.environ.get(var):
            logger.error(f"❌ Отсутствует переменная окружения: {var}")
            return
    
    if not os.path.exists(os.environ["CREDS_FILE"]):
        logger.error(f"❌ Файл учетных данных не найден: {os.environ['CREDS_FILE']}")
        return
    
    # Настройка обработчиков
    application = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
    
    # Обработчик для режима TR
    tr_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('tr', tr_mode)],
        states={
            TR_TYPE: [
                CommandHandler('work', tr_work),
                CommandHandler('out', tr_out),
                CommandHandler('cancel', cancel)
            ],
            WORK_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_work)],
            OUT_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_out)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('gim', gim_mode))
    application.add_handler(tr_conv_handler)
    
    # Запуск вебхука (со встроенным health check в PTB 20.x+)
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ["PORT"]),
        webhook_url=os.environ["WEBHOOK_URL"],
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
