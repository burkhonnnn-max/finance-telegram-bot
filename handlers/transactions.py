from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from states import TransactionState
from keyboards import (
    get_main_keyboard,
    get_cancel_reply_keyboard,
    get_categories_keyboard,
    get_comment_skip_keyboard,
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES
)
from utils import format_money, parse_amount, parse_quick_entry

router = Router()

# Callback data xaritasini hosil qilish
CATEGORY_NAMES = dict(EXPENSE_CATEGORIES + INCOME_CATEGORIES)


# 1. Tezkor yozuvlar: +50000 oylik yoki -15000 tushlik
@router.message(lambda msg: msg.text and (msg.text.startswith("+") or msg.text.startswith("-")))
async def handle_quick_entry(message: Message, state: FSMContext):
    # Agar foydalanuvchi biror holatda (FSM) bo'lsa, xalaqit bermaymiz
    current_state = await state.get_state()
    if current_state is not None:
        return

    parsed = parse_quick_entry(message.text)
    if not parsed:
        await message.answer(
            "⚠️ Summa noto'g'ri kiritildi.\nMasalan: <code>-15000 tushlik</code> yoki <code>+50000 oylik</code>",
            parse_mode="HTML"
        )
        return

    tr_type = parsed["type"]
    amount = parsed["amount"]
    category = parsed["category"]
    comment = parsed["comment"]

    # Bazaga yozish
    tx_id = await db.add_transaction(
        user_id=message.from_user.id,
        tr_type=tr_type,
        amount=amount,
        category=category,
        comment=comment
    )

    balance_info = await db.get_balance(message.from_user.id)

    sign = "🟢 +" if tr_type == "income" else "🔴 -"
    type_label = "Kirim" if tr_type == "income" else "Chiqim"
    
    response = (
        f"✅ <b>{type_label} muvaffaqiyatli saqlandi!</b>\n\n"
        f"💵 <b>Summa:</b> {sign}{format_money(amount)}\n"
        f"🏷 <b>Toifa:</b> {category}\n"
    )
    if comment:
        response += f"📝 <b>Izoh:</b> {comment}\n"
    
    response += f"\n💰 <b>Joriy sof balans:</b> {format_money(balance_info['balance'])}"

    await message.answer(response, reply_markup=get_main_keyboard(), parse_mode="HTML")


# 2. Tugma orqali Kirim yoki Chiqim boshlash
@router.message(F.text == "➕ Kirim qo'shish")
async def start_income(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(tr_type="income")
    await state.set_state(TransactionState.amount)
    await message.answer(
        "🟢 <b>Kirim summasini kiriting:</b>\n\n"
        "<i>Masalan: 100000, 100k yoki 1.5mln</i>",
        reply_markup=get_cancel_reply_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "➖ Chiqim qo'shish")
async def start_expense(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(tr_type="expense")
    await state.set_state(TransactionState.amount)
    await message.answer(
        "🔴 <b>Chiqim summasini kiriting:</b>\n\n"
        "<i>Masalan: 25000, 25k yoki 50000</i>",
        reply_markup=get_cancel_reply_keyboard(),
        parse_mode="HTML"
    )


# 3. Summani qabul qilish va Toifani so'rash
@router.message(TransactionState.amount)
async def process_amount(message: Message, state: FSMContext):
    # Bekor qilish tugmasi bosilgan bo'lsa
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Amal bekor qilindi.", reply_markup=get_main_keyboard())
        return

    amount = parse_amount(message.text)
    if not amount or amount <= 0:
        await message.answer(
            "⚠️ Iltimos, summani to'g'ri formatda kiriting (musbat son bo'lishi kerak).\n"
            "Masalan: <code>50000</code> yoki <code>50k</code>",
            parse_mode="HTML"
        )
        return

    data = await state.get_data()
    tr_type = data.get("tr_type", "expense")

    await state.update_data(amount=amount)
    await state.set_state(TransactionState.category)

    type_word = "Kirim" if tr_type == "income" else "Chiqim"
    await message.answer(
        f"💵 <b>Summa:</b> {format_money(amount)}\n\n"
        f"Endi ushbu {type_word.lower()} uchun <b>toifani (kategoriyani)</b> tanlang:",
        reply_markup=get_categories_keyboard(tr_type),
        parse_mode="HTML"
    )


# 4. Toifa tanlanganda
@router.callback_query(TransactionState.category, F.data.startswith("cat_"))
async def process_category(callback: CallbackQuery, state: FSMContext):
    category_name = CATEGORY_NAMES.get(callback.data, "Boshqa")
    await state.update_data(category=category_name)
    await state.set_state(TransactionState.comment)

    await callback.message.edit_text(
        f"🏷 <b>Tanlangan toifa:</b> {category_name}\n\n"
        f"Endi ushbu amal uchun <b>izoh (eslatma)</b> yozib qoldirishingiz mumkin.\n"
        f"Agar izoh kerak bo'lmasa, <b>'O'tkazib yuborish'</b> tugmasini bosing:",
        reply_markup=get_comment_skip_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# 5. Izohni o'tkazib yuborish (Skip)
@router.callback_query(TransactionState.comment, F.data == "skip_comment")
async def process_skip_comment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id

    tx_id = await db.add_transaction(
        user_id=user_id,
        tr_type=data["tr_type"],
        amount=data["amount"],
        category=data["category"],
        comment=None
    )

    await finish_transaction(callback.message, user_id, data, None)
    await state.clear()
    await callback.answer()


# 6. Izohni matn sifatida qabul qilish
@router.message(TransactionState.comment)
async def process_comment(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Amal bekor qilindi.", reply_markup=get_main_keyboard())
        return

    data = await state.get_data()
    user_id = message.from_user.id
    comment = message.text.strip()

    await db.add_transaction(
        user_id=user_id,
        tr_type=data["tr_type"],
        amount=data["amount"],
        category=data["category"],
        comment=comment
    )

    await finish_transaction(message, user_id, data, comment)
    await state.clear()


async def finish_transaction(target_msg: Message, user_id: int, data: dict, comment: str | None):
    """Tranzaksiya saqlangandan so'ng xulosa chiqarish"""
    balance_info = await db.get_balance(user_id)
    tr_type = data["tr_type"]
    sign = "🟢 +" if tr_type == "income" else "🔴 -"
    type_label = "Kirim" if tr_type == "income" else "Chiqim"

    text = (
        f"✅ <b>{type_label} muvaffaqiyatli saqlandi!</b>\n\n"
        f"💵 <b>Summa:</b> {sign}{format_money(data['amount'])}\n"
        f"🏷 <b>Toifa:</b> {data['category']}\n"
    )
    if comment:
        text += f"📝 <b>Izoh:</b> {comment}\n"
    
    text += f"\n💰 <b>Joriy sof balans:</b> {format_money(balance_info['balance'])}"

    await target_msg.answer(text, reply_markup=get_main_keyboard(), parse_mode="HTML")
