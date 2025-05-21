import requests
from config import OPENROUTER_API_KEY

def generate_text_openrouter(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://yourproject.com"  # Можна будь-що або залишити
    }

    payload = {
        "model": "meta-llama/llama-3-8b-instruct",  # Назва моделі
        "messages": [
            {"role": "system",
             "content": "Ти — бот автострахування. Відповідай коротко та по суті, лише на задане запитання, українською мовою. Не додавай зайвих фраз чи питань у кінці."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"].strip()
            content += "\n\nЯкщо у вас запитань більше немає, очікую від вас фото документів."
            return content
        else:
            return "⚠️ Помилка від AI. Спробуй пізніше."
    except Exception:
        return "⚠️ Виникла помилка при зверненні до OpenRouter."
