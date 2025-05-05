import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
MIND_API_KEY = os.getenv("MIND_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
