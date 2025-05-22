import requests, time
from config import MIND_API_KEY
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# === Надсилання документів ===
def process_document(document_path):
    """Надсилає документ до Mindee API для асинхронної обробки."""
    url = "https://api.mindee.net/v1/products/BOhdan2/passport_and_vehicle_document/v1/predict_async"
    headers = {"Authorization": f"Token {MIND_API_KEY}"}
    with open(document_path, "rb") as file:
        files = {"document": file}
        response = requests.post(url, headers=headers, files=files)
        return response.json() if response.status_code in [200, 202] else None

def check_processing_status(polling_url, headers):
    """Перевіряє статус обробки документа з паузою."""
    attempts = 0
    while attempts < 5:
        response = requests.get(polling_url, headers=headers)
        if response.status_code == 200:
            inference = response.json().get('document', {}).get('inference', {})
            if 'finished_at' in inference:
                return response.json()
        attempts += 1
        time.sleep(10)  # Чекаємо перед наступною спробою, щоб уникнути помилки 429 (Too Many Requests)
    return None

# === Основна обробка двох документів ===
async def extract_data_from_documents(update, context):
    passport_path = context.user_data.get('passport_path')
    vehicle_path = context.user_data.get('vehicle_path')

    all_data, error = {}, False

    # Обробка паспорта
    if passport_path:
        res = process_document(passport_path)
        if res:
            poll_url = res['job']['polling_url']
            headers = {"Authorization": f"Token {MIND_API_KEY}"}
            stat = check_processing_status(poll_url, headers)
            if stat:
                pred = stat.get('document', {}).get('inference', {}).get('prediction', {})
                all_data['ПІБ'] = pred.get('full_name', {}).get('value')
                all_data['Номер паспорта'] = pred.get('passport_number', {}).get('value')
            else:
                error = True
        else:
            error = True

    # Обробка техпаспорта
    if vehicle_path:
        res = process_document(vehicle_path)
        if res:
            poll_url = res['job']['polling_url']
            headers = {"Authorization": f"Token {MIND_API_KEY}"}
            stat = check_processing_status(poll_url, headers)
            if stat:
                pred = stat.get('document', {}).get('inference', {}).get('prediction', {})
                all_data['Марка авто'] = pred.get('car_brand', {}).get('value')
                all_data['Номер авто'] = pred.get('car_number', {}).get('value')
            else:
                error = True
        else:
            error = True

    if error:
        await update.message.reply_text(
            "⚠️ Не вдалося розпізнати дані з документів.\n"
            "Будь ласка, надішли фото ще раз!"
        )
        context.user_data['state'] = 'waiting_passport'
        return

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
        [InlineKeyboardButton("✅ Так", callback_data="confirm_data"),
         InlineKeyboardButton("❌ Ні", callback_data="retry_data")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
