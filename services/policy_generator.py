import datetime

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
