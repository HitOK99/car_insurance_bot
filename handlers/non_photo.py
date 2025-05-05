from telegram import Update
from telegram.ext import ContextTypes
from services.ai_service import generate_text_openrouter

# === ОБРОБКА НЕ ФОТО ===
async def handle_non_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка текстових повідомлень та інших форматів, окрім фото."""

    message = update.message

    # Якщо користувач надіслав файл (document)
    if message.document:
        await message.reply_text(
            "⚠️ Будь ласка, надішли документ *як фото*, а не як файл.\n"
            "Використай 📎 і вибери *Галерея* або *Камера*.",
            parse_mode="Markdown"
        )
        return

    # Якщо користувач надіслав відео
    if message.video:
        await message.reply_text(
            "⚠️ Відео не підтримується. Надішли фото документа.",
            parse_mode="Markdown"
        )
        return

    # Якщо користувач надіслав текст — обробляємо через AI
    if message.text:
        user_text = message.text
        await message.chat.send_action(action="typing") # Показує "друкує..."

        # Створюємо промпт для AI
        prompt = f"{user_text}"

        ai_response = generate_text_openrouter(prompt)
        await message.reply_text(ai_response)
