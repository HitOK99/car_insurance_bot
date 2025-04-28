from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
import os
from dotenv import load_dotenv
import datetime
import requests
import time

# === ЗАВАНТАЖЕННЯ ТОКЕНІВ ===
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
MIND_API_KEY = os.getenv("MIND_API_KEY")


def process_document(document_path):
    """Надсилає документ до Mindee API для асинхронної обробки."""
    url = "https://api.mindee.net/v1/products/bohdan-buryhin/passport_and_vehicle_document/v1/predict_async"
    headers = {
        "Authorization": f"Token {MIND_API_KEY}",
    }

    with open(document_path, "rb") as file:
        files = {"document": file}
        response = requests.post(url, headers=headers, files=files)

        if response.status_code in [200, 202]:
            return response.json()
        else:
            return None


def check_processing_status(polling_url, headers):
    """Перевіряє статус обробки документа з паузою між запитами."""
    attempts = 0

    while attempts < 5:
        response = requests.get(polling_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            inference = data.get('document', {}).get('inference', {})
            if 'finished_at' in inference:
                return data
        attempts += 1
        time.sleep(10)  # Чекаємо перед наступною спробою, щоб уникнути помилки 429 (Too Many Requests)

    return None

# === СТАРТ ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Я бот для покупки автострахування 🚗💼\n"
        "Надішли мені фото свого паспорта, будь ласка."
    )
    context.user_data['state'] = 'waiting_passport'


async def extract_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    passport_path = context.user_data.get('passport_path')
    vehicle_path = context.user_data.get('vehicle_path')

    all_data = {}
    error_occurred = False

    # Обробка паспорта
    if passport_path:
        result_passport = process_document(passport_path)
        if result_passport:
            polling_url = result_passport['job']['polling_url']
            headers = {"Authorization": f"Token {MIND_API_KEY}"}
            status_data = check_processing_status(polling_url, headers)
            if status_data:
                prediction = status_data.get('document', {}).get('inference', {}).get('prediction', {})
                all_data['ПІБ'] = prediction.get('full_name', {}).get('value')
                all_data['Номер паспорта'] = prediction.get('passport_number', {}).get('value')
            else:
                error_occurred = True
        else:
            error_occurred = True

    # Обробка техпаспорта
    if vehicle_path:
        result_vehicle = process_document(vehicle_path)
        if result_vehicle:
            polling_url = result_vehicle['job']['polling_url']
            headers = {"Authorization": f"Token {MIND_API_KEY}"}
            status_data = check_processing_status(polling_url, headers)
            if status_data:
                prediction = status_data.get('document', {}).get('inference', {}).get('prediction', {})
                all_data['Марка авто'] = prediction.get('car_brand', {}).get('value')
                all_data['Номер авто'] = prediction.get('car_number', {}).get('value')
            else:
                error_occurred = True
        else:
            error_occurred = True

    if error_occurred:
        await update.message.reply_text(
            "⚠️ Не вдалося розпізнати дані з документів.\n"
            "Будь ласка, надішли фото ще раз!"
        )
        context.user_data['state'] = 'waiting_passport'
        return

    # Якщо все добре
    extracted_data = {
        "ПІБ": all_data.get("ПІБ") or "Не вказано",
        "Номер паспорта": all_data.get("Номер паспорта") or "Не вказано",
        "Марка авто": all_data.get("Марка авто") or "Не вказано",
        "Номер авто": all_data.get("Номер авто") or "Не вказано",
    }

    context.user_data['extracted_data'] = extracted_data

    text = "Я знайшов таку інформацію з документів 📄:\n\n"
    for k, v in extracted_data.items():
        text += f"{k}: {v}\n"
    text += "\nВсе вірно?"

    keyboard = [
        [
            InlineKeyboardButton("✅ Так", callback_data="confirm_data"),
            InlineKeyboardButton("❌ Ні, перезавантажити", callback_data="retry_data")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, reply_markup=reply_markup)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    state = context.user_data.get('state')

    photo = update.message.photo[-1]
    file = await photo.get_file()

    os.makedirs(f"photos/{user_id}", exist_ok=True)

    if state == 'waiting_passport':
        passport_path = f"photos/{user_id}/passport.jpg"
        await file.download_to_drive(passport_path)
        context.user_data['passport_path'] = passport_path

        await update.message.reply_text("Дякую! Тепер надішли, будь ласка, фото техпаспорта 🚘")
        context.user_data['state'] = 'waiting_vehicle_doc'

    elif state == 'waiting_vehicle_doc':
        vehicle_path = f"photos/{user_id}/vehicle.jpg"
        await file.download_to_drive(vehicle_path)
        context.user_data['vehicle_path'] = vehicle_path

        await update.message.reply_text("Отримав обидва документи! 🔍 Обробляю дані...")

        # Переходимо до обробки обох документів
        await extract_data(update, context)

    else:
        await update.message.reply_text("Будь ласка, почніть з /start")


# === ОБРОБКА НЕ ФОТО ===
async def handle_non_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚠️ Будь ласка, надішли документ *як фото*, а не як файл, текст чи щось інше.\n"
        "Використай 📎 і вибери *Галерея* або *Камера*.",
        parse_mode="Markdown"
    )


# === ГЕНЕРАЦІЯ ПОЛІСУ ===
async def generate_policy(extracted_data):
    current_date = datetime.datetime.now().strftime("%d.%m.%Y")
    return (
        f"🔒 *Страховий поліс №CAR-{extracted_data['Номер авто'].replace(' ', '')}*\n\n"
        f"👤 *ПІБ:* {extracted_data['ПІБ']}\n"
        f"🪪 *Паспорт:* {extracted_data['Номер паспорта']}\n"
        f"🚗 *Автомобіль:* {extracted_data['Марка авто']} ({extracted_data['Номер авто']})\n"
        f"💵 *Сума страхування:* 100 USD\n"
        f"📅 *Дата оформлення:* {current_date}\n\n"
        "✅ Поліс дійсний і буде надісланий вам на email після оплати.\n"
        "_(Це тестова версія полісу, згенерована без OpenAI)_"
    )


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
        await query.edit_message_text("Окей, надішли, будь ласка, фото паспорта ще раз 📷")

    elif data == "agree_price":
        await query.edit_message_text("Чудово! Генерую твій страховий поліс... 📄")
        context.user_data['state'] = 'policy_generated'

        extracted_data = context.user_data.get('extracted_data')
        policy_text = await generate_policy(extracted_data)

        await query.message.reply_text(policy_text, parse_mode="Markdown")

    elif data == "decline_price":
        await query.edit_message_text(
            "На жаль, ціна *100 USD* є фіксованою і не підлягає зміні 😔",
            parse_mode="Markdown"
        )


# === MAIN ===
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
