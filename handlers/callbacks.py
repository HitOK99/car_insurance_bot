from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from services.policy_generator import generate_policy

# === CALLBACK ОБРОБКА ===
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "confirm_data":
        await query.edit_message_text("Дякую за підтвердження ✅")
        context.user_data['state'] = 'price_offer'

        keyboard = [
            [
                InlineKeyboardButton("✅ Згоден", callback_data="agree_price"),
                InlineKeyboardButton("❌ Не згоден", callback_data="decline_price")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "Вартість автострахування складає *100 USD* 💵\nПогоджуєшся з цією ціною?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    elif data == "retry_data":
        context.user_data['state'] = 'waiting_passport'
        await query.edit_message_text(
            "Окей, надішли, будь ласка, фото паспорта ще раз 📷.\n"
            "Якщо виникли труднощі при обробленні фото, спробуйте надіслати трохи інше — наприклад, зробити фото ближче або з кращою видимістю тексту. Це може покращити розпізнавання даних."
        )

    elif data == "agree_price":
        await query.edit_message_text("Чудово! Генерую твій страховий поліс... 📄")
        context.user_data['state'] = 'policy_generated'

        extracted_data = context.user_data.get('extracted_data')
        policy_text = await generate_policy(extracted_data)
        await query.message.reply_text(policy_text, parse_mode="Markdown")

    elif data == "decline_price":
        await query.edit_message_text(
            "На жаль, ціна *100 USD* фіксована 😔",
            parse_mode="Markdown"
        )
