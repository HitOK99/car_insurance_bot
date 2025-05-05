import os
from telegram import Update
from telegram.ext import ContextTypes
from services.mindee_service import extract_data_from_documents

# === ОБРОБКА ФОТО ===
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
        await extract_data_from_documents(update, context)

    else:
        await update.message.reply_text("Будь ласка, почніть з /start")
