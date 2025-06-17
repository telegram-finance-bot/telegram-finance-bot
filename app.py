append_row(row, value_input_option="USER_ENTERED")

    elif user_data["mode"] == "TR":
        if user_data["work_type"].upper() == "WORK":
            row = [
                now, user_data["name"], user_data["work_type"], user_data["bt"],
                "", "", user_data["card"], "", "", "", user_data["helper_name"],
                user_data["earned"], "", "", "", "", user_data["time"]
            ]
            sheet.worksheet("TR").append_row(row, value_input_option="USER_ENTERED")
        elif user_data["work_type"].upper() == "OUT":
            row = [""] * 18 + [user_data["earned"], user_data["time"]]
            sheet.worksheet("TR").append_row(row, value_input_option="USER_ENTERED")

    await update.message.reply_text("Данные сохранены.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
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
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    await app.bot.set_webhook("https://telegram-finance-bot-0ify.onrender.com")

    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url="https://telegram-finance-bot-0ify.onrender.com",
        webhook_path="/"
    )

if name == "__main__":
    asyncio.run(main())
