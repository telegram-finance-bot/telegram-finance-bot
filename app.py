import os
import json
import gspread
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound

# ===== Логгер =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== Проверка окружения =====
def check_environment():
    required_vars = {
        'BOT_TOKEN': os.environ.get("BOT_TOKEN"),
        'SHEET_ID': os.environ.get("SHEET_ID"),
        'CREDS_FILE': os.environ.get("CREDS_FILE"),
        'WEBHOOK_URL': os.environ.get("WEBHOOK_URL"),
        'PORT': os.environ.get("PORT", "10000")
    }
    
    logger.info("Проверка переменных окружения:")
    for key, value in required_vars.items():
        status = "✓" if value else "✗"
        logger.info(f"{key}: {status}")
    
    if not all(required_vars.values()):
        missing = [k for k, v in required_vars.items() if not v]
        logger.error(f"Отсутствуют переменные: {', '.join(missing)}")
        return False
    
    if not os.path.exists(required_vars['CREDS_FILE']):
        logger.error(f"Файл учетных данных не найден: {required_vars['CREDS_FILE']}")
        return False
    
    return True

# ===== Google Sheets init =====
def init_google_sheets():
    try:
        creds_file = os.environ.get("CREDS_FILE")
        sheet_id = os.environ.get("SHEET_ID")
        
        with open(creds_file) as f:
            creds_data = json.load(f)
        
        credentials = Credentials.from_service_account_info(
            creds_data,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.file"
            ]
        )
        
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(sheet_id)
        logger.info(f"Успешно подключено к таблице: {sheet.title}")
        
        for sheet_name in ['GIM', 'TR']:
            try:
                sheet.worksheet(sheet_name)
            except WorksheetNotFound:
                sheet.add_worksheet(title=sheet_name, rows=100, cols=20)
                logger.info(f"Создан новый лист: {sheet_name}")
        
        return sheet
        
    except Exception as e:
        logger.error(f"Ошибка при работе с Google Sheets: {str(e)}")
        return None

# ===== Обработчики команд =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен! Используйте /help для списка команд.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
    Доступные команды:
    /start - Запустить бота
    /help - Показать это сообщение
    """
    await update.message.reply_text(help_text)

# ===== Основная функция =====
def main():
    if not check_environment():
        raise RuntimeError("Проверка окружения не пройдена")
    
    sheet = init_google_sheets()
    if not sheet:
        raise RuntimeError("Не удалось инициализировать Google Sheets")
    
    try:
        application = ApplicationBuilder().token(os.environ.get("BOT_TOKEN")).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        
        application.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT")),
            webhook_url=os.environ.get("WEBHOOK_URL"),
            drop_pending_updates=True
        )
        
        logger.info("Бот успешно запущен в режиме webhook")
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}")
        raise

if __name__ == "__main__":
    main()
