import os
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)

# === ENVIRONMENT VARIABLES ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GOOGLE_KEY_FILE = "gspread_key.json"
SPREADSHEET_NAME = "ESOPLAN"

# === STATES ===
MODE, SUBMODE, GIM_DATE, GIM_NAME, GIM_TYPE, GIM_IN, GIM_HELPER, GIM_EARNED, TR_DATE, TR_NAME, TR_TYPE, TR_BT, TR_CARD, TR_HELPER, TR_EARNED, TR_EQUIP, TR_MAINT, TR_GAS, TR_FINE, TR_BONUS, TR_TIME = range(21)

# === GOOGLE SHEETS SETUP ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_KEY_FILE, scope)
client = gspread.authorize(creds)
sheet = client.open(SPREADSHEET_NAME)
gim_ws = sheet.worksheet("GIM")
tr_ws = sheet.worksheet("TR")

user_data = {}

# === START ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите режим: GIM или TR")
    return MODE

# === MODE HANDLER ===
async def mode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.upper()
    if text == "GIM":
        user_data[update.effective_chat.id] = {"mode": "GIM"}
        await update.message.reply_text("Введите дату:")
        return GIM_DATE
    elif text == "TR":
        user_data[update.effective_chat.id] = {"mode": "TR"}
        await update.message.reply_text("Введите подрежим: WORK или OUT")
        return SUBMODE
    else:
        await update.message.reply_text("Пожалуйста, введите GIM или TR")
        return MODE

# === GIM FLOW ===
async def gim_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["date"] = update.message.text
    await update.message.reply_text("Введите имя:")
    return GIM_NAME

async def gim_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["name"] = update.message.text
    await update.message.reply_text("Введите тип работы:")
    return GIM_TYPE

async def gim_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["type"] = update.message.text
    await update.message.reply_text("Введите сумму IN:")
    return GIM_IN

async def gim_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["in"] = update.message.text
    await update.message.reply_text("Введите помощника:")
    return GIM_HELPER

async def gim_helper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["helper"] = update.message.text
    await update.message.reply_text("Введите заработанное:")
    return GIM_EARNED

async def gim_earned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["earned"] = update.message.text
    data = user_data[update.effective_chat.id]
    gim_ws.append_row([data["date"], data["name"], data["type"], data["in"], "", "", data["helper"], data["earned"]])
    await update.message.reply_text("✅ Данные GIM сохранены.")
    return ConversationHandler.END

# === TR FLOW ===
async def submode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    submode = update.message.text.upper()
    user_data[update.effective_chat.id]["submode"] = submode
    await update.message.reply_text("Введите дату:")
    return TR_DATE

async def tr_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["date"] = update.message.text
    await update.message.reply_text("Введите имя:")
    return TR_NAME

async def tr_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["name"] = update.message.text
    await update.message.reply_text("Введите тип работы:")
    return TR_TYPE

async def tr_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["type"] = update.message.text
    await update.message.reply_text("Введите BT:")
    return TR_BT

async def tr_bt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["bt"] = update.message.text
    await update.message.reply_text("Введите карту:")
    return TR_CARD

async def tr_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["card"] = update.message.text
    await update.message.reply_text("Введите помощника:")
    return TR_HELPER

async def tr_helper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["helper"] = update.message.text
    await update.message.reply_text("Введите заработанное:")
    return TR_EARNED

async def tr_earned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["earned"] = update.message.text
    if user_data[update.effective_chat.id]["submode"] == "OUT":
        tr_ws.append_row([
            user_data[update.effective_chat.id]["date"],
            user_data[update.effective_chat.id]["name"],
            user_data[update.effective_chat.id]["type"],
            "", "", user_data[update.effective_chat.id]["card"],
            user_data[update.effective_chat.id]["helper"],
            user_data[update.effective_chat.id]["earned"]
        ])
        await update.message.reply_text("✅ Данные TR/OUT сохранены.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Введите время:")
        return TR_TIME

async def tr_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["time"] = update.message.text
    await update.message.reply_text("Введите оборудование:")
    return TR_EQUIP

async def tr_equip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["equip"] = update.message.text
    await update.message.reply_text("Введите обслуживание:")
    return TR_MAINT

async def tr_maint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["maint"] = update.message.text
    await update.message.reply_text("Введите бензин:")
    return TR_GAS

async def tr_gas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["gas"] = update.message.text
    await update.message.reply_text("Введите штраф:")
    return TR_FINE

async def tr_fine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["fine"] = update.message.text
    await update.message.reply_text("Введите бонус:")
    return TR_BONUS

async def tr_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id]["bonus"] = update.message.text
    d = user_data[update.effective_chat.id]
    tr_ws.append_row([
        d["date"], d["name"], d["type"], d["bt"], "", d["card"],
        d["helper"], d["earned"], d["equip"], d["maint"], d["gas"],
        d["time"], d["fine"], d["bonus"]
    ])
    await update.message.reply_text("✅ Данные TR/WORK сохранены.")
    return ConversationHandler.END

# === CANCEL ===
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END

# === MAIN ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, mode_handler)],
            SUBMODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, submode_handler)],
            GIM_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, gim_date)],
            GIM_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, gim_name)],
            GIM_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, gim_type)],
            GIM_IN: [MessageHandler(filters.TEXT & ~filters.COMMAND, gim_in)],
            GIM_HELPER: [MessageHandler(filters.TEXT & ~filters.COMMAND, gim_helper)],
            GIM_EARNED: [MessageHandler(filters.TEXT & ~filters.COMMAND, gim_earned)],
            TR_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tr_date)],
            TR_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, tr_name)],
            TR_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tr_type)],
            TR_BT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tr_bt)],
            TR_CARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, tr_card)],
            TR_HELPER: [MessageHandler(filters.TEXT & ~filters.COMMAND, tr_helper)],
            TR_EARNED: [MessageHandler(filters.TEXT & ~filters.COMMAND, tr_earned)],
            TR_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, tr_time)],
            TR_EQUIP: [MessageHandler(filters.TEXT & ~filters.COMMAND, tr_equip)],
            TR_MAINT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tr_maint)],
            TR_GAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, tr_gas)],
            TR_FINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tr_fine)],
            TR_BONUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, tr_bonus)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
