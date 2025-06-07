import os
import json
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Настройки — теперь через переменные окружения
TOKEN = os.getenv("TOKEN")
SPREADSHEET_NAME = os.getenv("SHEET_NAME")
CREDS_FILE = os.getenv("CREDS_FILE")

# Константы состояний
(
    CHOOSE_MODE,
    CHOOSE_TYPE,
    ENTER_DATE,
    ENTER_NAME,
    ENTER_WORK_TYPE,
    ENTER_BT,
    ENTER_CARD,
    ENTER_HELPER,
    ENTER_EARNED,
    ENTER_EQUIPMENT,
    ENTER_MAINTENANCE,
    ENTER_GAS,
    ENTER_TIME,
    ENTER_FINE,
    ENTER_BONUS,
    ENTER_RENT,
    ENTER_UTIL,
    ENTER_CAR,
    ENTER_NEED,
    ENTER_FOOD,
    ENTER_OT,
    ENTER_DINCEL,
) = range(22)

user_data_dict = {}

# Инициализация Google Sheets
def init_sheet(sheet_type="TR"):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME)
    return sheet.worksheet(sheet_type)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Привет! Напиши GIM или TR, чтобы выбрать режим.")
    return CHOOSE_MODE

# Обработка режима
async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    mode = update.message.text.strip().upper()
    context.user_data.clear()

    if mode == "GIM":
        await update.message.reply_text("Введите Rent:")
        return ENTER_RENT
    elif mode == "TR":
        await update.message.reply_text("TR выбран. Напишите WORK или OUT.")
        return CHOOSE_TYPE
    else:
        await update.message.reply_text("Пожалуйста, напиши GIM или TR.")
        return CHOOSE_MODE

# Обработка TR типа
async def choose_tr_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    mode = update.message.text.strip().upper()

    if mode == "WORK":
        await update.message.reply_text("Введите дату:")
        return ENTER_DATE
    elif mode == "OUT":
        await update.message.reply_text("Введите equipment:")
        return ENTER_EQUIPMENT
    else:
        await update.message.reply_text("Пожалуйста, напиши WORK или OUT.")
        return CHOOSE_TYPE

# Ввод для WORK
async def enter_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["date"] = update.message.text
    await update.message.reply_text("Введите имя:")
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Введите work type:")
    return ENTER_WORK_TYPE

async def enter_work_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["work_type"] = update.message.text
    await update.message.reply_text("Введите BT:")
    return ENTER_BT

async def enter_bt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["bt"] = update.message.text
    await update.message.reply_text("Введите card:")
    return ENTER_CARD

async def enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["card"] = update.message.text
    await update.message.reply_text("Введите helper name:")
    return ENTER_HELPER

async def enter_helper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["helper"] = update.message.text
    await update.message.reply_text("Введите what they earned:")
    return ENTER_EARNED

async def enter_earned(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["earned"] = update.message.text

    sheet = init_sheet("TR")
    row = [
        context.user_data.get("date", ""),
        context.user_data.get("name", ""),
        context.user_data.get("work_type", ""),
        context.user_data.get("bt", ""),
        "", "",  # E, F пропущены
        context.user_data.get("card", ""),
        context.user_data.get("helper", ""),
        context.user_data.get("earned", ""),
    ]
    sheet.append_row(row)
    await update.message.reply_text("Данные успешно записаны.")
    return ConversationHandler.END

# Ввод для OUT
async def enter_equipment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["equipment"] = update.message.text
    await update.message.reply_text("Введите maintenance:")
    return ENTER_MAINTENANCE

async def enter_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["maintenance"] = update.message.text
    await update.message.reply_text("Введите gas:")
    return ENTER_GAS

async def enter_gas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["gas"] = update.message.text
    await update.message.reply_text("Введите time:")
    return ENTER_TIME

async def enter_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["time"] = update.message.text
    await update.message.reply_text("Введите fine:")
    return ENTER_FINE

async def enter_fine(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["fine"] = update.message.text
    await update.message.reply_text("Введите bonus:")
    return ENTER_BONUS

async def enter_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["bonus"] = update.message.text

    sheet = init_sheet("TR")
    row = ["" for _ in range(10)] + [
        context.user_data.get("equipment", ""),
        context.user_data.get("maintenance", ""),
        context.user_data.get("gas", ""),
        context.user_data.get("time", ""),
        context.user_data.get("fine", ""),
        context.user_data.get("bonus", "")
    ]
    sheet.append_row(row)
    await update.message.reply_text("Данные успешно записаны.")
    return ConversationHandler.END

# Ввод для GIM (оставим нетронутым)
async def enter_rent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["rent"] = update.message.text
    await update.message.reply_text("Введите utility:")
    return ENTER_UTIL

async def enter_util(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["util"] = update.message.text
    await update.message.reply_text("Введите car:")
    return ENTER_CAR

async def enter_car(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["car"] = update.message.text
    await update.message.reply_text("Введите need:")
    return ENTER_NEED

async def enter_need(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["need"] = update.message.text
    await update.message.reply_text("Введите food:")
    return ENTER_FOOD

async def enter_food(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["food"] = update.message.text
    await update.message.reply_text("Введите ot:")
    return ENTER_OT

async def enter_ot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["ot"] = update.message.text
    await update.message.reply_text("Введите dincel:")
    return ENTER_DINCEL

async def enter_dincel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["dincel"] = update.message.text
    sheet = init_sheet("GIM")
    row = [
        "", context.user_data.get("rent", ""),
        context.user_data.get("util", ""),
        context.user_data.get("car", ""),
        context.user_data.get("need", ""),
        context.user_data.get("food", ""),
        context.user_data.get("ot", ""),
        context.user_data.get("dincel", "")
    ]
    sheet.append_row(row)
    await update.message.reply_text("Данные успешно записаны.")
    return ConversationHandler.END

# Основной запуск
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_mode)],
            CHOOSE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_tr_type)],
            ENTER_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_date)],
            ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
            ENTER_WORK_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_work_type)],
            ENTER_BT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_bt)],
            ENTER_CARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_card)],
            ENTER_HELPER: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_helper)],
            ENTER_EARNED: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_earned)],
            ENTER_EQUIPMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_equipment)],
            ENTER_MAINTENANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_maintenance)],
            ENTER_GAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_gas)],
            ENTER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_time)],
            ENTER_FINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_fine)],
            ENTER_BONUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_bonus)],
            ENTER_RENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_rent)],
            ENTER_UTIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_util)],
            ENTER_CAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_car)],
            ENTER_NEED: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_need)],
            ENTER_FOOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_food)],
            ENTER_OT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_ot)],
            ENTER_DINCEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_dincel)],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
