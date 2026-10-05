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
)
from utils import format_money, parse_amount, parse_quick_entry
from ai_voice import parse_financial_intent, extract_number_from_text
import pending_manager as pm
from locales import t

logger = logging.getLogger(__name__)
router = Router()

MENU_BUTTONS = {
    "💰 Kirim", "💳 Chiqim", "➕ Kirim qo'shish", "➖ Chiqim qo'shish",
    "💰 Доход", "💳 Расход", "➕ Доход", "➖ Расход",
    "📊 Statistika & Hisobot", "📊 Statistika", "📊 Статистика и отчёты", "📊 Статистика",
    "💰 Mening balansim", "💵 Mening balansim", "💰 Мой баланс",
    "🕒 Oxirgi amallar", "🕒 История операций",
    "ℹ️ Qanday ishlatiladi?", "ℹ️ Yordam", "ℹ️ Помощь",
    "🌐 Til / Язык",
    "❌ Bekor qilish", "❌ Отмена"
}


# =========================================================================
# 1. DOIMIY MENYUDAGI "💰 Kirim / Доход" VA "💳 Chiqim / Расход"
# =========================================================================

@router.message(F.text.in_({"💰 Kirim", "➕ Kirim qo'shish", "💰 Доход", "➕ Доход"}))
async def start_income(message: Message, state: FSMContext):
    """Kirim / Доход tugmasi bosilganda"""
    await state.clear()
    await state.update_data(tr_type="income")
    await state.set_state(TransactionState.waiting_input)

    user_lang = (await db.get_user_language(message.from_user.id)) or "uz"
    await message.answer(
        t("income_prompt", user_lang),
        reply_markup=get_main_keyboard(user_lang),
        parse_mode="HTML"
    )


@router.message(F.text.in_({"💳 Chiqim", "➖ Chiqim qo'shish", "💳 Расход", "➖ Расход"}))
async def start_expense(message: Message, state: FSMContext):
    """Chiqim / Расход tugmasi bosilganda"""
    await state.clear()
    await state.update_data(tr_type="expense")
    await state.set_state(TransactionState.waiting_input)

    user_lang = (await db.get_user_language(message.from_user.id)) or "uz"
    await message.answer(
        t("expense_prompt", user_lang),
        reply_markup=get_main_keyboard(user_lang),
        parse_mode="HTML"
    )


# =========================================================================
# 2. KIRIM YOKI CHIQIM BOSILGANDAN SO'NG MATN KELGANDA
# =========================================================================

@router.message(TransactionState.waiting_input, F.text)
async def process_waiting_input(message: Message, state: FSMContext):
    user_lang = (await db.get_user_language(message.from_user.id)) or "uz"

    # Agar bekor qilish so'ralsa
    if message.text in ("❌ Bekor qilish", "❌ Отмена", "/cancel"):
        await state.clear()
        await message.answer(t("cancelled", user_lang), reply_markup=get_main_keyboard(user_lang))
        return

    # Agar boshqa menyu tugmasi bosilgan bo'lsa
    if message.text in MENU_BUTTONS:
        await state.clear()
        return

    state_data = await state.get_data()
    tr_type = state_data.get("tr_type", "expense")

    parsed = parse_financial_intent(message.text, forced_type=tr_type)
    if not parsed.get("is_finance") or not parsed.get("amount"):
        err_msg = (
            "⚠️ Сумма не найдена.\n\nПожалуйста, укажите также сумму, например:\n• <code>25000 обед</code>\n• <code>50k продукты</code>\n• <code>100000</code>"
            if user_lang == "ru"
            else "⚠️ Summa aniqlanmadi.\n\nIltimos, summani ham kiriting, masalan:\n• <code>25000 tushlik</code>\n• <code>50k bozorlik</code>\n• <code>100000</code>"
        )
        await message.answer(err_msg, parse_mode="HTML")
        return

    await state.clear()

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
    summary_text = pm.format_summary(pending_data, is_fix_mode=False, lang=user_lang)

    await message.answer(
        summary_text,
        reply_markup=get_confirm_keyboard(pending_id, lang=user_lang),
        parse_mode="HTML"
    )


# =========================================================================
# 3. HECH QANDAY TUGMA BOSILMASDAN MATN YUBORILGANDA
# =========================================================================

# A. Tezkor belgi bilan boshlangan matn (+50000 oylik yoki -15000 tushlik)
@router.message(lambda msg: msg.text and (msg.text.startswith("+") or msg.text.startswith("-")))
async def handle_quick_entry(message: Message, state: FSMContext):
    await state.clear()
    user_lang = (await db.get_user_language(message.from_user.id)) or "uz"

    parsed = parse_quick_entry(message.text)
    if not parsed:
        err_msg = (
            "⚠️ Неверный формат суммы.\nНапример: <code>-15000 обед</code> или <code>+50000 зарплата</code>"
            if user_lang == "ru"
            else "⚠️ Summa noto'g'ri kiritildi.\nMasalan: <code>-15000 tushlik</code> yoki <code>+50000 oylik</code>"
        )
        await message.answer(err_msg, parse_mode="HTML")
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
    summary_text = pm.format_summary(pending_data, is_fix_mode=False, lang=user_lang)

    await message.answer(
        summary_text,
        reply_markup=get_confirm_keyboard(pending_id, lang=user_lang),
        parse_mode="HTML"
    )


# B. Oddiy matn xabari (ichida summa va maqsad aytilgan bo'lsa)
@router.message(F.text & ~F.text.startswith("/") & ~F.text.in_(MENU_BUTTONS))
async def handle_general_text_entry(message: Message, state: FSMContext):
    amount = extract_number_from_text(message.text)
    if not amount or amount <= 0:
        return

    user_lang = (await db.get_user_language(message.from_user.id)) or "uz"
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
    summary_text = pm.format_summary(pending_data, is_fix_mode=False, lang=user_lang)

    await message.answer(
        summary_text,
        reply_markup=get_confirm_keyboard(pending_id, lang=user_lang),
        parse_mode="HTML"
    )
