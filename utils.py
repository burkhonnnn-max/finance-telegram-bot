import re
from typing import Optional, Tuple, Dict, Any


def format_money(amount: float) -> str:
    """Summani chiroyli probellar bilan formatlash (masalan: 120 000 so'm)"""
    if amount == int(amount):
        formatted = f"{int(amount):,}".replace(",", " ")
    else:
        formatted = f"{amount:,.2f}".replace(",", " ")
    return f"{formatted} so'm"


def parse_amount(text: str) -> Optional[float]:
    """Foydalanuvchi kiritgan summani songa aylantirish (masalan: 50000, 50 000, 50k, 1.5mln, 100 тыс)"""
    from ai_voice import extract_number_from_text
    return extract_number_from_text(text)


def parse_quick_entry(text: str) -> Optional[Dict[str, Any]]:
    """
    Tezkor yozuvni aniqlash:
    +50000 Oylik maosh
    + 100k Frilans
    -15000 Tushlik
    - 20k Taxi
    """
    text = text.strip()
    if not (text.startswith("+") or text.startswith("-")):
        return None
    
    tr_type = "income" if text.startswith("+") else "expense"
    remaining = text[1:].strip()
    
    # Bo'sh joy bilan bo'lib birinchi qismini summa deb ko'ramiz
    parts = remaining.split(maxsplit=1)
    if not parts:
        return None
    
    amount = parse_amount(parts[0])
    if not amount or amount <= 0:
        return None
    
    comment = parts[1].strip() if len(parts) > 1 else None
    
    # Avtomatik toifa aniqlash (oddiy kalit so'zlar orqali)
    category = "📦 Boshqa kirim" if tr_type == "income" else "📦 Boshqa chiqim"
    if comment:
        low_comment = comment.lower()
        if tr_type == "expense":
            if any(w in low_comment for w in ["ovqat", "bozor", "non", "gosht", "go'sht", "suv", "choy", "osh"]):
                category = "🍽 Oziq-ovqat"
            elif any(w in low_comment for w in ["taxi", "taksi", "benzin", "yo'l", "yol", "avtobus", "metro"]):
                category = "🚕 Transport & Yo'l"
            elif any(w in low_comment for w in ["kafe", "restoran", "kofe", "coffee", "lunch", "tushlik"]):
                category = "☕️ Kafe & Restoran"
            elif any(w in low_comment for w in ["svet", "gaz", "suv", "kommunal", "ijara", "kvartira", "dom"]):
                category = "🏠 Uy & Kommunal"
            elif any(w in low_comment for w in ["kiyim", "shim", "koylak", "ko'ylak", "oyoqkiyim", "shop"]):
                category = "🛍 Kiyim & Xarid"
            elif any(w in low_comment for w in ["dori", "apteka", "doktor", "shifoxona", "klinika"]):
                category = "💊 Salomatlik & Dori"
            elif any(w in low_comment for w in ["internet", "paynet", "telefon", "megabayt", "tarif"]):
                category = "📱 Aloqa & Internet"
            elif any(w in low_comment for w in ["kino", "oyin", "o'yin", "game", "dam"]):
                category = "🎮 Ko'ngilochar"
            elif any(w in low_comment for w in ["ehson", "sadaqa", "sovga", "sovg'a", "hadya"]):
                category = "🎁 Ehson / Sovg'a"
        else:
            if any(w in low_comment for w in ["oylik", "maosh", "avans", "zp", "salary"]):
                category = "💼 Oylik maosh"
            elif any(w in low_comment for w in ["frilans", "loyiha", "mijoz", "dastur", "zakaz"]):
                category = "💻 Frilans / Biznes"
            elif any(w in low_comment for w in ["qarz", "qaytgan"]):
                category = "🔄 Qarz qaytishi"
            elif any(w in low_comment for w in ["sovga", "sovg'a", "mukofot"]):
                category = "🎁 Sovg'a / Yordam"
            elif any(w in low_comment for w in ["foyda", "savdo", "foiz"]):
                category = "📈 Savdo / Foyda"

    return {
        "type": tr_type,
        "amount": amount,
        "category": category,
        "comment": comment
    }


def generate_progress_bar(percentage: float, length: int = 8) -> str:
    """Foiz bo'yicha vizual progress bar hosil qilish: masalan [▓▓▓░░░░░]"""
    filled_len = int(round(length * (percentage / 100.0)))
    filled_len = max(0, min(length, filled_len))
    bar = "■" * filled_len + "□" * (length - filled_len)
    return bar


def get_tashkent_now():
    """Toshkent vaqti bo'yicha joriy vaqtni olish (UTC+5)"""
    from datetime import datetime
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Asia/Tashkent"))
    except Exception:
        from datetime import timezone, timedelta
        return datetime.now(timezone(timedelta(hours=5)))

