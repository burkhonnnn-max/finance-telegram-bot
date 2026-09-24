import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Agar token ko'rsatilmagan bo'lsa ogohlantirish
if not BOT_TOKEN:
    print("DIQQAT: .env faylida BOT_TOKEN ko'rsatilmagan! Iltimos, @BotFather'dan olgan tokeningizni kiriting.")

DB_PATH = os.getenv("DB_PATH", "finance_bot.db")
