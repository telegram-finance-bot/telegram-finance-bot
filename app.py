import os
import json
import gspread
import logging
from aiohttp import web
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound, APIError
from datetime import datetime

# === Логирование ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Константы ===
TR_TYPE, WORK_DATA, OUT_DATA = range(3)

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

        for name in ["GIM", "TR"]:
            try:
                sheet.worksheet(name)
            except WorksheetNotFound:
                sheet.add_worksheet(title=name, rows=100, cols=20)
                logger.info(f"Создан новый лист: {name}")
        return sheet
    except KeyError as e:
        logger.error(f"Ошибка: Переменная окружения {e} не найдена")
        raise
    except FileNotFoundError:
        logger.error(f"Файл учетных данных {os.environ.get('CREDS_FILE')} не найден")
        raise
    except Exception as e:
        logger.error(f"Ошибка при инициализации Google Sheets: {e}")
        raise

# === Telegram Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Выберите режим:\n/gim\n/tr")

async def gim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sheet = init_google_sheets().worksheet("GIM")
        sheet.append_row([datetime.now().isoformat(), update.effective_user.full_name])
        await update.message.reply_text("✅ GIM-запись добавлена.")
    except APIError as e:
        logger.error(f"Ошибка Google Sheets: {e}")
        await update.message.reply_text("❌ Ошибка при записи в Google Sheets.")
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}")
        await update.message.reply_text("❌ Произошла неизвестная ошибка.")

async def tr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите: /work или /out")
    return TR_TYPE

async def tr_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите WORK: Дата, Имя, Проект, Часы")
    return WORK_DATA

async def tr_out(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите OUT: Дата, Имя, Причина")
    return OUT_DATA

async def save_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = ["WORK"] + [x.strip() for x in update.message.text.split(",")]
        if len(data) != 5:  # Проверка на количество полей
            await update.message.reply_text("❌ Неверный формат. Ожидается: Дата, Имя, Проект, Часы")
            return WORK_DATA
        sheet = init_google_sheets().worksheet("TR")
        sheet.append_row(data)
        await update.message.reply_text("✅ WORK добавлен")
        return ConversationHandler.END
    except APIError as e:
        logger.error(f"Ошибка Google Sheets: {e}")
        await update.message.reply_text("❌ Ошибка при записи в Google Sheets.")
        return WORK_DATA
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}")
        await update.message.reply_text("❌ Произошла неизвестная ошибка.")
        return WORK_DATA

async def save_out(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = ["OUT"] + [x.strip() for x in update.message.text.split(",")]
        if len(data) != 4:  # Проверка на количество полей
            await update.message.reply_text("❌ Неверный формат. Ожидается: Дата, Имя, Причина")
            return OUT_DATA
        sheet = init_google_sheets().worksheet("TR")
        sheet.append_row(data)
        await update.message.reply_text("✅ OUT добавлен")
        return ConversationHandler.END
    except APIError as e:
        logger.error(f"Ошибка Google Sheets: {e}")
        await update.message.reply_text("❌ Ошибка при записи в Google Sheets.")
        return OUT_DATA
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}")
        await update.message.reply_text("❌ Произошла неизвестная ошибка.")
        return OUT_DATA

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

# === Health check ===
async def health_check(request):
    return web.Response(text="OK", status=200)

# === Webhook handler ===
async def handle_webhook(request):
    try:
        app = request.app["telegram_app"]
        update = Update.de_json(await request.json(), app.bot)
        await app.process_update(update)
        return web.Response(status=200)
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
        return web.Response(status=500)

# === Главная функция ===
async def main():
    try:
        # Telegram-бот
        app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()

        # Обработчики
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("tr", tr)],
            states={
                TR_TYPE: [
                    CommandHandler("work", tr_work),
                    CommandHandler("out", tr_out)
                ],
                WORK_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_work)],
                OUT_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_out)]
            },
            fallbacks=[CommandHandler("cancel", cancel)]
        )

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("gim", gim))
        app.add_handler(conv_handler)

        # Приложение aiohttp
        aio_app = web.Application()
        aio_app["telegram_app"] = app  # Сохраняем Telegram-бот для использования в вебхуке
        aio_app.add_routes([
            web.get("/", health_check),
            web.post("/webhook", handle_webhook)
        ])

        # Установка URL вебхука
        webhook_url = os.environ["WEBHOOK_URL"] + "/webhook"
        await app.bot.set_webhook(url=webhook_url)

        # Запуск сервера aiohttp
        runner = web.AppRunner(aio_app)
        await runner.setup()
        port = int(os.environ.get("PORT", 10000))
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"✅ Сервер aiohttp запущен на порту {port}")

        # Запуск Telegram-бота с polling
        await app.initialize()
        await app.start()
        logger.info("✅ Telegram-бот запущен")
        await app.run_polling()  # Используем run_polling вместо start_polling и wait_until_closed

    except Exception as e:
        logger.error(f"Ошибка в main: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
