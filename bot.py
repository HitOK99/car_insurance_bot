from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import TOKEN
from handlers.start import start
from handlers.photos import handle_photo
from handlers.non_photo import handle_non_photo
from handlers.callbacks import handle_callback

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(~filters.PHOTO & filters.ALL, handle_non_photo))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("Бот запущено...")
    app.run_polling()


if __name__ == "__main__":
    main()
