import uuid
from typing import Dict, Any, Optional
import database as db
from utils import format_money
from locales import t, localize_category

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


def format_summary(data: Dict[str, Any], is_fix_mode: bool = False, lang: str = "uz") -> str:
    """Foydalanuvchiga ko'rsatiladigan tasdiqlash kartochkasi (uz yoki ru)"""
    tr_type = data.get("type", "expense")
    amount = data.get("amount", 0.0)
    category = data.get("category", "")
    localized_cat = localize_category(category, lang)
    comment = data.get("comment", "")
    transcript = data.get("transcript", "")

    sign = "🟢" if tr_type == "income" else "🔴"
    type_label = t("income_name", lang) if tr_type == "income" else t("expense_name", lang)

    text = ""
    if transcript:
        heard_label = t("heard", lang)
        text += f"🎙 <b>{heard_label}:</b> «<i>{transcript}</i>»\n\n"

    text += f"📋 <b>{t('summary_title', lang)}</b>\n"
    text += f"   {sign} <b>{t('type_label', lang)}:</b> {type_label}\n"
    text += f"   💵 <b>{t('amount_label', lang)}:</b> {format_money(amount)}\n"
    text += f"   🏷 <b>{t('category_label', lang)}:</b> {localized_cat}\n"
    if comment:
        text += f"   📝 <b>{t('comment_label', lang)}:</b> {comment}\n"

    if is_fix_mode:
        text += f"\n✏️ <b>{t('which_part_question', lang)}</b>"
    else:
        text += f"\n<b>{t('is_correct_question', lang)}</b>"

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
