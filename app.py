import os
import json
import gspread
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)
from google.oauth2.service_account import Credentials

# === Переменные окружения ===
TOKEN = os.environ["BOT_TOKEN"]
SHEET_NAME = os.environ["SHEET_NAME"]
CREDS_FILE = os.environ["CREDS_FILE"]

# === Google Sheets ===
with open(CREDS_FILE) as f:
    creds_data = json.load(f)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
client = gspread.authorize(credentials)
sheet = client.open(SHEET_NAME)

# === Состояния ===
ENTER_NAME = 0

# === Хендлеры ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Введите ваше имя:")
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    sheet.worksheet("GIM").append_row([now, name], value_input_option="USER_ENTERED")
    await update.message.reply_text(f"✅ Сохранено: {name}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

# === Запуск приложения ===
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    await app.bot.set_webhook("https://telegram-finance-bot-0ify.onrender.com")
    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url="https://telegram-finance-bot-0ify.onrender.com"
    )

if __name__ == "__main__":
    import asyncio
    from nest_asyncio import apply
    apply()
    try:
        asyncio.run(main())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
