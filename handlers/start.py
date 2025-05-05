from telegram import Update
from telegram.ext import ContextTypes

# === СТАРТ ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Я бот для покупки автострахування 🚗💼\n"
        "Надішли мені фото свого паспорта, будь ласка."
    )
    context.user_data['state'] = 'waiting_passport'
