from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

import database as db
from keyboards import get_main_keyboard
from utils import format_money

router = Router()


@router.message(F.text == "🕒 Oxirgi amallar")
async def show_recent_history(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    transactions = await db.get_recent_transactions(user_id, limit=8)

    if not transactions:
        await message.answer(
            "🕒 Sizda hali hech qanday amallar tarixi mavjud emas.",
            reply_markup=get_main_keyboard()
        )
        return

    text = "🕒 <b>Oxirgi amallaringiz:</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    buttons = []

    for i, tx in enumerate(transactions, start=1):
        sign = "🟢 +" if tx["type"] == "income" else "🔴 -"
        comment_str = f" (<i>{tx['comment']}</i>)" if tx["comment"] else ""
        date_str = tx["created_at"][5:16] # MM-DD HH:MM

        text += (
            f"<b>{i}.</b> {sign}{format_money(tx['amount'])}\n"
            f"   🏷 {tx['category']}{comment_str}\n"
            f"   🕒 <i>{date_str}</i>\n\n"
        )
        buttons.append([
            InlineKeyboardButton(
                text=f"🗑 {i}-amalni o'chirish ({sign}{format_money(tx['amount'])})",
                callback_data=f"del_tx_{tx['id']}"
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("del_tx_"))
async def process_delete_transaction(callback: CallbackQuery):
    user_id = callback.from_user.id
    tx_id = int(callback.data.replace("del_tx_", ""))

    tx = await db.get_transaction(tx_id, user_id)
    if not tx:
        await callback.answer("⚠️ Bu amal topilmadi yoki allaqachon o'chirilgan.", show_alert=True)
        return

    deleted = await db.delete_transaction(tx_id, user_id)
    if deleted:
        balance_info = await db.get_balance(user_id)
        sign = "+" if tx["type"] == "income" else "-"
        await callback.answer("✅ Amal muvaffaqiyatli o'chirildi!", show_alert=True)
        
        # Yangilangan ro'yxatni chiqarish
        transactions = await db.get_recent_transactions(user_id, limit=8)
        if not transactions:
            await callback.message.edit_text(
                f"🗑 <b>Amal ({sign}{format_money(tx['amount'])}) o'chirildi.</b>\n\n"
                f"Sizda boshqa amallar qolmadi.\n"
                f"💰 Yangi balans: <b>{format_money(balance_info['balance'])}</b>",
                parse_mode="HTML"
            )
            return

        text = (
            f"🗑 <b>Amal ({sign}{format_money(tx['amount'])}) o'chirildi.</b>\n"
            f"💰 Yangi balans: <b>{format_money(balance_info['balance'])}</b>\n\n"
            f"🕒 <b>Qolgan oxirgi amallaringiz:</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        )
        buttons = []
        for i, t in enumerate(transactions, start=1):
            s = "🟢 +" if t["type"] == "income" else "🔴 -"
            comment_str = f" (<i>{t['comment']}</i>)" if t["comment"] else ""
            date_str = t["created_at"][5:16]

            text += (
                f"<b>{i}.</b> {s}{format_money(t['amount'])}\n"
                f"   🏷 {t['category']}{comment_str}\n"
                f"   🕒 <i>{date_str}</i>\n\n"
            )
            buttons.append([
                InlineKeyboardButton(
                    text=f"🗑 {i}-amalni o'chirish ({s}{format_money(t['amount'])})",
                    callback_data=f"del_tx_{t['id']}"
                )
            ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await callback.answer("Xatolik yuz berdi.", show_alert=True)
