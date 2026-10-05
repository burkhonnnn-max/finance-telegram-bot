import uuid
from typing import Dict, Any, Optional
import database as db
from utils import format_money

# Xotirada vaqtinchalik tasdiqlashni kutayotgan tranzaksiyalar
# {pending_id: {user_id, full_name, username, type, amount, category, comment, transcript}}
_pending_items: Dict[str, Dict[str, Any]] = {}


def create_pending(
    user_id: int,
    full_name: str,
    username: Optional[str],
    tr_type: str,
    amount: float,
    category: str,
    comment: str,
    transcript: Optional[str] = None
) -> str:
    """Yangi vaqtinchalik tranzaksiya yaratish va ID sini qaytarish"""
    pending_id = uuid.uuid4().hex[:8]
    _pending_items[pending_id] = {
        "id": pending_id,
        "user_id": user_id,
        "full_name": full_name or "",
        "username": username or "",
        "type": tr_type,
        "amount": float(amount),
        "category": category,
        "comment": comment or "",
        "transcript": transcript or ""
    }
    return pending_id


def get_pending(pending_id: str) -> Optional[Dict[str, Any]]:
    """Vaqtinchalik tranzaksiya ma'lumotlarini olish"""
    return _pending_items.get(pending_id)


def pop_pending(pending_id: str) -> Optional[Dict[str, Any]]:
    """Vaqtinchalik tranzaksiyani o'chirib olish"""
    return _pending_items.pop(pending_id, None)


def delete_pending(pending_id: str):
    """Vaqtinchalik tranzaksiyani o'chirish"""
    _pending_items.pop(pending_id, None)


def format_summary(data: Dict[str, Any], is_fix_mode: bool = False) -> str:
    """Foydalanuvchiga ko'rsatiladigan tasdiqlash kartochkasi"""
    tr_type = data.get("type", "expense")
    amount = data.get("amount", 0.0)
    category = data.get("category", "")
    comment = data.get("comment", "")
    transcript = data.get("transcript", "")

    sign = "🟢" if tr_type == "income" else "🔴"
    type_label = "Kirim" if tr_type == "income" else "Chiqim"

    text = ""
    if transcript:
        text += f"🎙 <b>Eshitildi:</b> «<i>{transcript}</i>»\n\n"

    text += f"📋 <b>Aniqlangan ma'lumot:</b>\n"
    text += f"   {sign} <b>Tur:</b> {type_label}\n"
    text += f"   💵 <b>Summa:</b> {format_money(amount)}\n"
    text += f"   🏷 <b>Toifa:</b> {category}\n"
    if comment:
        text += f"   📝 <b>Izoh/Maqsad:</b> {comment}\n"

    if is_fix_mode:
        text += "\n✏️ <b>Qaysi qismini o'zgartirmoqchisiz?</b>"
    else:
        text += "\n<b>Ma'lumotlar to'g'rimi?</b>"

    return text


async def save_pending_to_db(data: Dict[str, Any]) -> Dict[str, Any]:
    """Tasdiqlangan ma'lumotni bazaga saqlash"""
    user_id = data["user_id"]
    await db.add_user(
        user_id=user_id,
        full_name=data.get("full_name", ""),
        username=data.get("username", "")
    )
    tx_id = await db.add_transaction(
        user_id=user_id,
        tr_type=data["type"],
        amount=data["amount"],
        category=data["category"],
        comment=data.get("comment") or None
    )
    balance_info = await db.get_balance(user_id)
    return {
        "tx_id": tx_id,
        "balance_info": balance_info
    }
