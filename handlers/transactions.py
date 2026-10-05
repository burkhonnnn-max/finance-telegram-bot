import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from states import TransactionState
from keyboards import (
    get_main_keyboard,
    get_confirm_keyboard,
    get_type_keyboard,
    get_categories_keyboard,
    get_comment_skip_keyboard,
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES
)
from utils import format_money, parse_amount, parse_quick_entry
from ai_voice import parse_financial_intent, extract_number_from_text
import pending_manager as pm

logger = logging.getLogger(__name__)
router = Router()

CATEGORY_NAMES = dict(EXPENSE_CATEGORIES + INCOME_CATEGORIES)


# =========================================================================
# 1. DOIMIY MENYUDAGI "💰 Kirim" VA "💳 Chiqim" TUGMALARI
# =========================================================================

@router.message(F.text.in_({"💰 Kirim", "➕ Kirim qo'shish"}))
async def start_income(message: Message, state: FSMContext):
    """Foydalanuvchi quyi menyudan Kirim tugmasini bosganda"""
    await state.clear()
    await state.update_data(tr_type="income")
    await state.set_state(TransactionState.waiting_input)

    await message.answer(
        "🟢 <b>Kirim bo'limi tanlandi!</b>\n\n"
        "Iltimos, summani va nima uchunligini <b>yozing</b> (masalan: <i>'500 000 oylik'</i> yoki <i>'100k frilans'</i>)\n"
        "yoki 🎙 <b>ovozli xabar</b> yuboring:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text.in_({"💳 Chiqim", "➖ Chiqim qo'shish"}))
async def start_expense(message: Message, state: FSMContext):
    """Foydalanuvchi quyi menyudan Chiqim tugmasini bosganda"""
    await state.clear()
    await state.update_data(tr_type="expense")
    await state.set_state(TransactionState.waiting_input)

    await message.answer(
        "🔴 <b>Chiqim bo'limi tanlandi!</b>\n\n"
        "Iltimos, summani va nima uchunligini <b>yozing</b> (masalan: <i>'25 000 tushlik'</i> yoki <i>'15k taxi'</i>)\n"
        "yoki 🎙 <b>ovozli xabar</b> yuboring:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


# =========================================================================
# 2. KIRIM YOKI CHIQIM BOSILGANDAN SO'NG MATN KELGANDA
# =========================================================================

@router.message(TransactionState.waiting_input, F.text)
async def process_waiting_input(message: Message, state: FSMContext):
    # Agar bekor qilish so'ralsa
    if message.text in ("❌ Bekor qilish", "/cancel"):
        await state.clear()
        await message.answer("Amal bekor qilindi.", reply_markup=get_main_keyboard())
        return

    # Agar boshqa bo'lim tugmasi bosilgan bo'lsa
    if message.text in ("📊 Statistika & Hisobot", "💰 Mening balansim", "💵 Mening balansim", "🕒 Oxirgi amallar", "ℹ️ Qanday ishlatiladi?"):
        await state.clear()
        return

    state_data = await state.get_data()
    tr_type = state_data.get("tr_type", "expense")

    parsed = parse_financial_intent(message.text, forced_type=tr_type)
    if not parsed.get("is_finance") or not parsed.get("amount"):
        await message.answer(
            "⚠️ Summa aniqlanmadi.\n\n"
            "Iltimos, summani ham kiriting, masalan:\n"
            "• <code>25000 tushlik</code>\n"
            "• <code>50k bozorlik</code>\n"
            "• <code>100000</code>",
            parse_mode="HTML"
        )
        return

    await state.clear()

    # Tasdiqlash uchun vaqtinchalik saqlash
    amount = parsed["amount"]
    category = parsed.get("category") or ("📦 Boshqa kirim" if tr_type == "income" else "📦 Boshqa chiqim")
    comment = parsed.get("comment", "")

    pending_id = pm.create_pending(
        user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
        tr_type=tr_type,
        amount=amount,
        category=category,
        comment=comment,
        transcript=None
    )

    pending_data = pm.get_pending(pending_id)
    summary_text = pm.format_summary(pending_data, is_fix_mode=False)

    await message.answer(
        summary_text,
        reply_markup=get_confirm_keyboard(pending_id),
        parse_mode="HTML"
    )


# =========================================================================
# 3. HECH QANDAY TUGMA BOSILMASDAN MATN YUBORILGANDA
# =========================================================================

# A. Tezkor belgi bilan boshlangan matn (+50000 oylik yoki -15000 tushlik)
@router.message(lambda msg: msg.text and (msg.text.startswith("+") or msg.text.startswith("-")))
async def handle_quick_entry(message: Message, state: FSMContext):
    await state.clear()
    parsed = parse_quick_entry(message.text)
    if not parsed:
        await message.answer(
            "⚠️ Summa noto'g'ri kiritildi.\nMasalan: <code>-15000 tushlik</code> yoki <code>+50000 oylik</code>",
            parse_mode="HTML"
        )
        return

    pending_id = pm.create_pending(
        user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
        tr_type=parsed["type"],
        amount=parsed["amount"],
        category=parsed["category"],
        comment=parsed["comment"] or "",
        transcript=None
    )

    pending_data = pm.get_pending(pending_id)
    summary_text = pm.format_summary(pending_data, is_fix_mode=False)

    await message.answer(
        summary_text,
        reply_markup=get_confirm_keyboard(pending_id),
        parse_mode="HTML"
    )


MENU_BUTTONS = {
    "💰 Kirim", "💳 Chiqim", "➕ Kirim qo'shish", "➖ Chiqim qo'shish",
    "📊 Statistika & Hisobot", "📊 Statistika",
    "💰 Mening balansim", "💵 Mening balansim",
    "🕒 Oxirgi amallar", "ℹ️ Qanday ishlatiladi?", "ℹ️ Yordam", "❌ Bekor qilish"
}


# B. Oddiy matn xabari (ichida summa va maqsad aytilgan bo'lsa)
@router.message(F.text & ~F.text.startswith("/") & ~F.text.in_(MENU_BUTTONS))
async def handle_general_text_entry(message: Message, state: FSMContext):
    # Summa bor-yo'qligini tekshirish
    amount = extract_number_from_text(message.text)
    if not amount or amount <= 0:
        return

    parsed = parse_financial_intent(message.text)
    tr_type = parsed.get("type", "expense")
    category = parsed.get("category", "📦 Boshqa chiqim")
    comment = parsed.get("comment", message.text)

    pending_id = pm.create_pending(
        user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
        tr_type=tr_type,
        amount=amount,
        category=category,
        comment=comment,
        transcript=None
    )

    pending_data = pm.get_pending(pending_id)
    summary_text = pm.format_summary(pending_data, is_fix_mode=False)

    await message.answer(
        summary_text,
        reply_markup=get_confirm_keyboard(pending_id),
        parse_mode="HTML"
    )
