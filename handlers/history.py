from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

import database as db
from keyboards import get_main_keyboard
from utils import format_money
from locales import t, localize_category

router = Router()


@router.message(F.text.in_({"🕒 Oxirgi amallar", "🕒 История операций"}))
async def show_recent_history(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    transactions = await db.get_recent_transactions(user_id, limit=8)

    if not transactions:
        await message.answer(
            t("no_history", user_lang),
            reply_markup=get_main_keyboard(user_lang)
        )
        return

    title = "🕒 <b>Ваши последние операции:</b>\n━━━━━━━━━━━━━━━━━━━━\n" if user_lang == "ru" else "🕒 <b>Oxirgi amallaringiz:</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    text = title
    buttons = []

    for i, tx in enumerate(transactions, start=1):
        sign = "🟢 +" if tx["type"] == "income" else "🔴 -"
        comment_str = f" (<i>{tx['comment']}</i>)" if tx["comment"] else ""
        date_str = tx["created_at"][5:16]  # MM-DD HH:MM
        cat_name = localize_category(tx['category'], user_lang)

        text += (
            f"<b>{i}.</b> {sign}{format_money(tx['amount'])}\n"
            f"   🏷 {cat_name}{comment_str}\n"
            f"   🕒 <i>{date_str}</i>\n\n"
        )
        del_label = f"🗑 Удалить #{i} ({sign}{format_money(tx['amount'])})" if user_lang == "ru" else f"🗑 {i}-amalni o'chirish ({sign}{format_money(tx['amount'])})"
        buttons.append([
            InlineKeyboardButton(
                text=del_label,
                callback_data=f"del_tx_{tx['id']}"
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("del_tx_"))
async def process_delete_transaction(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    tx_id = int(callback.data.replace("del_tx_", ""))

    tx = await db.get_transaction(tx_id, user_id)
    if not tx:
        not_found_msg = "⚠️ Операция не найдена или уже удалена." if user_lang == "ru" else "⚠️ Bu amal topilmadi yoki allaqachon o'chirilgan."
        await callback.answer(not_found_msg, show_alert=True)
        return

    deleted = await db.delete_transaction(tx_id, user_id)
    if deleted:
        await callback.answer(t("deleted_success", user_lang), show_alert=False)
        # Tarixni qayta yangilab ko'rsatish
        transactions = await db.get_recent_transactions(user_id, limit=8)
        if not transactions:
            await callback.message.edit_text(t("no_history", user_lang))
            return

        title = "🕒 <b>Ваши последние операции:</b>\n━━━━━━━━━━━━━━━━━━━━\n" if user_lang == "ru" else "🕒 <b>Oxirgi amallaringiz:</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        text = title
        buttons = []
        for i, t_row in enumerate(transactions, start=1):
            sign = "🟢 +" if t_row["type"] == "income" else "🔴 -"
            comment_str = f" (<i>{t_row['comment']}</i>)" if t_row["comment"] else ""
            date_str = t_row["created_at"][5:16]
            cat_name = localize_category(t_row['category'], user_lang)
            text += (
                f"<b>{i}.</b> {sign}{format_money(t_row['amount'])}\n"
                f"   🏷 {cat_name}{comment_str}\n"
                f"   🕒 <i>{date_str}</i>\n\n"
            )
            del_label = f"🗑 Удалить #{i} ({sign}{format_money(t_row['amount'])})" if user_lang == "ru" else f"🗑 {i}-amalni o'chirish ({sign}{format_money(t_row['amount'])})"
            buttons.append([
                InlineKeyboardButton(
                    text=del_label,
                    callback_data=f"del_tx_{t_row['id']}"
                )
            ])
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
