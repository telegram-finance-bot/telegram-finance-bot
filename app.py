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
import logging
from gspread.exceptions import APIError, SpreadsheetNotFound

# ===== НАСТРОЙКА ЛОГГИРОВАНИЯ =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ =====
try:
    TOKEN = os.environ['BOT_TOKEN']
    CREDS_FILE = os.environ['CREDS_FILE']
    SPREADSHEET_NAME = os.environ['SHEET_NAME']
except KeyError as e:
    logger.error(f"Отсутствует переменная окружения: {e}")
    exit(1)

# ===== ИНИЦИАЛИЗАЦИЯ GOOGLE SHEETS =====
try:
    # Загрузка учетных данных
    if not os.path.exists(CREDS_FILE):
        raise FileNotFoundError(f"Файл учетных данных '{CREDS_FILE}' не найден")
    
    with open(CREDS_FILE) as f:
        data = json.load(f)
    
    # Авторизация
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(data, scopes=scopes)
    client = gspread.authorize(credentials)
    
    # Открытие таблицы
    try:
        sheet = client.open(SPREADSHEET_NAME)
        # Проверка наличия необходимых листов
        for worksheet_name in ['GIM', 'TR']:
            try:
                sheet.worksheet(worksheet_name)
            except gspread.WorksheetNotFound:
                logger.warning(f"Лист '{worksheet_name}' не найден, создаем...")
                sheet.add_worksheet(title=worksheet_name, rows=100, cols=20)
        
        logger.info("Google Sheets успешно инициализирован")
        
    except SpreadsheetNotFound:
        logger.error(f"Таблица '{SPREADSHEET_NAME}' не найдена")
        exit(1)
    except APIError as e:
        logger.error(f"Ошибка API Google Sheets: {e}")
        exit(1)

except Exception as e:
    logger.error(f"Ошибка инициализации Google Sheets: {e}")
    exit(1)

# ===== СОСТОЯНИЯ БОТА =====
(
    CHOOSE_MODE, ENTER_DATE, ENTER_NAME, ENTER_WORK_TYPE,
    ENTER_BT, ENTER_CARD, ENTER_HELPER_NAME, 
    ENTER_EARNED, ENTER_TIME
) = range(9)

# ===== ОСНОВНЫЕ ФУНКЦИИ БОТА =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало работы с ботом"""
    try:
        await update.message.reply_text(
            "Добро пожаловать! Выберите режим работы:\n"
            "• GIM - для работы в зале\n"
            "• TR - для тренировок"
        )
        return CHOOSE_MODE
    except Exception as e:
        logger.error(f"Ошибка в start: {e}")
        return ConversationHandler.END

async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора режима"""
    try:
        mode = update.message.text.strip().upper()
        if mode not in ['GIM', 'TR']:
            await update.message.reply_text("Пожалуйста, выберите GIM или TR")
            return CHOOSE_MODE
            
        context.user_data["mode"] = mode
        await update.message.reply_text("Введите дату в формате ДД.ММ (например: 15.06)")
        return ENTER_DATE
    except Exception as e:
        logger.error(f"Ошибка в choose_mode: {e}")
        await update.message.reply_text("Произошла ошибка, попробуйте снова")
        return CHOOSE_MODE

# ... (аналогичные обработчики для других состояний с try-except)

async def enter_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Финальное сохранение данных"""
    try:
        context.user_data["time"] = update.message.text
        user_data = context.user_data
        
        # Подготовка данных
        now = datetime.now().strftime("%d.%m")
        row_data = [
            now,
            user_data.get("name", ""),
            user_data.get("work_type", ""),
            user_data.get("bt", ""),
            user_data.get("card", ""),
            user_data.get("helper_name", ""),
            user_data.get("earned", ""),
            user_data.get("time", "")
        ]
        
        # Получение нужного листа
        worksheet = sheet.worksheet(user_data["mode"])
        
        # Добавление строки
        worksheet.append_row(row_data)
        
        await update.message.reply_text(
            "✅ Данные успешно сохранены!\n"
            f"Режим: {user_data['mode']}\n"
            f"Дата: {now}\n"
            f"Имя: {user_data.get('name', '')}"
        )
        
    except APIError as e:
        logger.error(f"Ошибка Google Sheets: {e}")
        await update.message.reply_text("❌ Ошибка при сохранении в Google Sheets")
    except Exception as e:
        logger.error(f"Ошибка в enter_time: {e}")
        await update.message.reply_text("❌ Произошла ошибка при сохранении")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена операции"""
    await update.message.reply_text("Операция отменена")
    return ConversationHandler.END

# ===== ЗАПУСК БОТА =====
def main():
    try:
        # Создаем приложение бота
        app = ApplicationBuilder().token(TOKEN).build()
        
        # Настройка обработчика диалога
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                CHOOSE_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_mode)],
                ENTER_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_date)],
                # ... другие состояния
                ENTER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_time)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )
        
        app.add_handler(conv_handler)
        
        logger.info("Бот запускается...")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}")
        exit(1)

if __name__ == "__main__":
    main()
