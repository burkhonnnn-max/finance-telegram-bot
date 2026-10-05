# -*- coding: utf-8 -*-
"""
Amallar tarixi va boshqaruvi (Pagination & Deletion & Month Reset)
Foydalanuvchiga joriy oy boshidan boshlab bugungacha kiritilgan barcha amallarni
tartib raqami (nomeratsiya), turi, summasi, maqsadi va vaqti bilan 10 tadan sahifalab ko'rsatadi.
Keraksiz amallarni raqamli tugmalar orqali bittalab o'chirish yoki butun oyni 0 dan tozalash imkonini beradi.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, Command

import database as db
from keyboards import get_main_keyboard
from utils import format_money, get_tashkent_now
from locales import t, localize_category
from excel_generator import MONTHS_UZ, MONTHS_RU

router = Router()

PER_PAGE = 10


async def build_history_response(user_id: int, user_lang: str, page: int = 1):
    """
    Joriy oy amallarini sahifalab (pagination) chiqarish uchun matn va klaviaturani yaratadi.
    """
    now = get_tashkent_now()
    year = now.year
    month = now.month
    is_ru = (user_lang == "ru")
    month_name = MONTHS_RU.get(month, "") if is_ru else MONTHS_UZ.get(month, "")

    all_txs = await db.get_month_transactions(user_id, year, month)
    total_items = len(all_txs)

    if total_items == 0:
        empty_text = (
            f"📋 <b>{month_name} {year}</b>:\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>В этом месяце операций пока нет (0 сум).</i>"
            if is_ru else
            f"📋 <b>{year}-yil {month_name} oyi</b>:\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Ushbu oyda hali hech qanday amal kiritilmagan (0 so'm).</i>"
        )
        empty_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📥 " + ("Excel скачать" if is_ru else "Excel hisobot"), callback_data="report_excel_current")],
                [InlineKeyboardButton(text="❌ " + ("Закрыть" if is_ru else "Yopish"), callback_data="hist_close")]
            ]
        )
        return empty_text, empty_kb

    total_pages = (total_items + PER_PAGE - 1) // PER_PAGE
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * PER_PAGE
    end_idx = min(start_idx + PER_PAGE, total_items)
    page_items = all_txs[start_idx:end_idx]

    # Matn sarlavhasi
    if is_ru:
        text = (
            f"📋 <b>Операции за {month_name} {year} г.:</b>\n"
            f"📄 <i>Страница {page}/{total_pages} (Всего операций: {total_items} шт.)</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )
    else:
        text = (
            f"📋 <b>{year}-yil {month_name} oyi amallari:</b>\n"
            f"📄 <i>Sahifa {page}/{total_pages} (Jami amallar: {total_items} ta)</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )

    # Amallar ro'yxati
    del_buttons = []
    current_row = []

    for idx, tx in enumerate(page_items):
        global_num = start_idx + idx + 1
        is_income = (tx["type"] == "income")
        sign_label = ("➕ Доход" if is_income else "➖ Расход") if is_ru else ("➕ Kirim" if is_income else "➖ Chiqim")
        amount_str = format_money(tx["amount"], lang=user_lang)
        cat_name = localize_category(tx["category"], user_lang)
        comment_val = tx["comment"] or ("-" if not is_ru else "без описания")
        
        # Sana va vaqt
        date_raw = tx["created_at"]
        try:
            # Format: YYYY-MM-DD HH:MM:SS -> DD.MM.YYYY HH:MM
            parts = date_raw.split(" ")
            ymd = parts[0].split("-")
            date_formatted = f"{ymd[2]}.{ymd[1]}.{ymd[0]} {parts[1][:5]}"
        except Exception:
            date_formatted = date_raw

        if is_ru:
            text += (
                f"<b>{global_num}.</b> {sign_label} | <b>{amount_str}</b>\n"
                f"   🏷 <b>Категория:</b> {cat_name}\n"
                f"   📝 <b>Назначение:</b> {comment_val}\n"
                f"   🕒 <b>Время:</b> {date_formatted}\n\n"
            )
        else:
            text += (
                f"<b>{global_num}.</b> {sign_label} | <b>{amount_str}</b>\n"
                f"   🏷 <b>Toifa:</b> {cat_name}\n"
                f"   📝 <b>Maqsad:</b> {comment_val}\n"
                f"   🕒 <b>Vaqti:</b> {date_formatted}\n\n"
            )

        # O'chirish tugmasi
        btn_label = f"🗑 #{global_num}"
        current_row.append(
            InlineKeyboardButton(
                text=btn_label,
                callback_data=f"ask_del_{tx['id']}_{global_num}_{page}"
            )
        )
        if len(current_row) == 5:
            del_buttons.append(current_row)
            current_row = []

    if current_row:
        del_buttons.append(current_row)

    # Pagination navigation tugmalari
    nav_row = []
    if total_pages > 1:
        if page > 1:
            nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi" if not is_ru else "⬅️ Назад", callback_data=f"hist_page_{page - 1}"))
        else:
            nav_row.append(InlineKeyboardButton(text="•", callback_data="hist_noop"))

        nav_row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="hist_noop"))

        if page < total_pages:
            nav_row.append(InlineKeyboardButton(text="Keyingi ➡️" if not is_ru else "Вперёд ➡️", callback_data=f"hist_page_{page + 1}"))
        else:
            nav_row.append(InlineKeyboardButton(text="•", callback_data="hist_noop"))

    keyboard_rows = []
    # 1. Tanlangan raqamni o'chirish tugmalari
    keyboard_rows.extend(del_buttons)

    # 2. Sahifalash tugmalari
    if nav_row:
        keyboard_rows.append(nav_row)

    # 3. Butun oyni tozalash (0 dan boshlash) va Excel
    reset_label = "🗑 Oyni tozalash (0 ga tushirish)" if not is_ru else "🗑 Очистить месяц (Сброс в 0)"
    excel_label = "📥 Excel hisobot (.xlsx)" if not is_ru else "📥 Скачать Excel (.xlsx)"
    close_label = "❌ Yopish" if not is_ru else "❌ Закрыть"

    keyboard_rows.append([
        InlineKeyboardButton(text=reset_label, callback_data="ask_reset_month"),
        InlineKeyboardButton(text=excel_label, callback_data="report_excel_current")
    ])
    keyboard_rows.append([
        InlineKeyboardButton(text=close_label, callback_data="hist_close")
    ])

    return text, InlineKeyboardMarkup(inline_keyboard=keyboard_rows)


@router.message(F.text.in_({"🕒 Oxirgi amallar", "🕒 История операций"}), StateFilter("*"))
@router.message(Command("history"), StateFilter("*"))
async def show_monthly_history(message: Message, state: FSMContext):
    """Joriy oy amallari boshqaruvi va ro'yxatini ochish"""
    await state.clear()
    user_id = message.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"

    text, kb = await build_history_response(user_id, user_lang, page=1)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("hist_page_"))
async def process_history_page(callback: CallbackQuery):
    """Sahifani almashtirish (oldinga / orqaga)"""
    user_id = callback.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    try:
        page = int(callback.data.replace("hist_page_", ""))
    except ValueError:
        page = 1

    text, kb = await build_history_response(user_id, user_lang, page=page)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "hist_noop")
async def process_history_noop(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data == "hist_close")
async def process_history_close(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer()


# ==========================================================
# AYRIM BOSHQA AMALNI O'CHIRISH (Confirmation card)
# ==========================================================
@router.callback_query(F.data.startswith("ask_del_"))
async def ask_delete_single_tx(callback: CallbackQuery):
    """Aynan bitta raqamdagi amalni o'chirishni tasdiqlash oynasi"""
    user_id = callback.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    is_ru = (user_lang == "ru")

    # callback_data: ask_del_{tx_id}_{global_num}_{page}
    parts = callback.data.split("_")
    tx_id = int(parts[2])
    global_num = parts[3]
    page = int(parts[4])

    tx = await db.get_transaction(tx_id, user_id)
    if not tx:
        not_found_msg = "⚠️ Bu amal topilmadi yoki allaqachon o'chirilgan." if not is_ru else "⚠️ Операция не найдена или уже удалена."
        await callback.answer(not_found_msg, show_alert=True)
        text, kb = await build_history_response(user_id, user_lang, page=page)
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        return

    is_income = (tx["type"] == "income")
    sign_label = ("➕ Доход" if is_income else "➖ Расход") if is_ru else ("➕ Kirim" if is_income else "➖ Chiqim")
    amount_str = format_money(tx["amount"], lang=user_lang)
    cat_name = localize_category(tx["category"], user_lang)
    comment_val = tx["comment"] or "-"
    date_val = tx["created_at"]

    if is_ru:
        card_text = (
            f"⚠️ <b>Вы действительно хотите удалить запись #{global_num}?</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 <b>Тип:</b> {sign_label}\n"
            f"💰 <b>Сумма:</b> <b>{amount_str}</b>\n"
            f"🏷 <b>Категория:</b> {cat_name}\n"
            f"📝 <b>Назначение:</b> {comment_val}\n"
            f"🕒 <b>Время:</b> {date_val}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Данное действие невозможно отменить!</i>"
        )
        confirm_btn = "🗑 Да, удалить"
        cancel_btn = "⬅️ Отмена"
    else:
        card_text = (
            f"⚠️ <b>Haqiqatan ham #{global_num}-amalni o'chirmoqchimisiz?</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 <b>Turi:</b> {sign_label}\n"
            f"💰 <b>Summa:</b> <b>{amount_str}</b>\n"
            f"🏷 <b>Toifa:</b> {cat_name}\n"
            f"📝 <b>Maqsad:</b> {comment_val}\n"
            f"🕒 <b>Vaqti:</b> {date_val}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Ushbu amalni ortga qaytarib bo'lmaydi!</i>"
        )
        confirm_btn = "🗑 Ha, o'chirilsin"
        cancel_btn = "⬅️ Bekor qilish"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=confirm_btn, callback_data=f"do_del_{tx_id}_{page}"),
                InlineKeyboardButton(text=cancel_btn, callback_data=f"hist_page_{page}")
            ]
        ]
    )
    await callback.message.edit_text(card_text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("do_del_"))
async def execute_delete_single_tx(callback: CallbackQuery):
    """Aynan bitta amalni bazadan o'chirish"""
    user_id = callback.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    is_ru = (user_lang == "ru")

    # callback_data: do_del_{tx_id}_{page}
    parts = callback.data.split("_")
    tx_id = int(parts[2])
    page = int(parts[3])

    await db.delete_transaction(tx_id, user_id)
    alert_msg = "✅ Операция успешно удалена!" if is_ru else "✅ Amal muvaffaqiyatli o'chirildi!"
    await callback.answer(alert_msg, show_alert=False)

    # Ro'yxatni yangilab ko'rsatish
    text, kb = await build_history_response(user_id, user_lang, page=page)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


# ==========================================================
# BUTUN OYNI TOZALASH (0 DAN BOSHLASH - RESET MONTH)
# ==========================================================
@router.message(Command("reset_month"), StateFilter("*"))
async def cmd_reset_month(message: Message, state: FSMContext):
    """Oy amallarini 0 ga tushirish buyrug'i"""
    await state.clear()
    user_id = message.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    is_ru = (user_lang == "ru")
    now = get_tashkent_now()
    month_name = MONTHS_RU.get(now.month, "") if is_ru else MONTHS_UZ.get(now.month, "")

    if is_ru:
        warn_text = (
            f"⚠️ <b>ВНИМАНИЕ! СБРОС И ОЧИСТКА МЕСЯЦА</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Вы уверены, что хотите удалить ВСЕ операции за <b>{month_name} {now.year}</b> г. и начать учёт <b>с 0</b>?\n\n"
            f"❗️ <i>Все ваши доходы и расходы за этот месяц будут безвозвратно удалены!</i>"
        )
        confirm_btn = "⚠️ Да, очистить месяц (Сбросить в 0)"
        cancel_btn = "❌ Отмена"
    else:
        warn_text = (
            f"⚠️ <b>DIQQAT! JORIY OYNI TOZALASH</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Siz haqiqatan ham <b>{now.year}-yil {month_name}</b> oyidagi barcha amallarni o'chirib, hisob-kitobni <b>0 dan</b> boshlamoqchimisiz?\n\n"
            f"❗️ <i>Ushbu oydagi barcha kirim va chiqimlaringiz o'chib ketadi. Ortga qaytarib bo'lmaydi!</i>"
        )
        confirm_btn = "⚠️ Ha, oyni tozalash (0 dan boshlash)"
        cancel_btn = "❌ Bekor qilish"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=confirm_btn, callback_data="do_reset_month")],
            [InlineKeyboardButton(text=cancel_btn, callback_data="hist_close")]
        ]
    )
    await message.answer(warn_text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "ask_reset_month")
async def ask_reset_month_callback(callback: CallbackQuery):
    """Inline tugma orqali oyni tozalash so'rovi"""
    user_id = callback.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    is_ru = (user_lang == "ru")
    now = get_tashkent_now()
    month_name = MONTHS_RU.get(now.month, "") if is_ru else MONTHS_UZ.get(now.month, "")

    if is_ru:
        warn_text = (
            f"⚠️ <b>ВНИМАНИЕ! СБРОС И ОЧИСТКА МЕСЯЦА</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Вы уверены, что хотите удалить ВСЕ операции за <b>{month_name} {now.year}</b> г. и начать учёт <b>с 0</b>?\n\n"
            f"❗️ <i>Все ваши доходы и расходы за этот месяц будут безвозвратно удалены!</i>"
        )
        confirm_btn = "⚠️ Да, очистить всё (Сбросить в 0)"
        cancel_btn = "⬅️ Отмена"
    else:
        warn_text = (
            f"⚠️ <b>DIQQAT! JORIY OYNI TOZALASH</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Siz haqiqatan ham <b>{now.year}-yil {month_name}</b> oyidagi barcha amallarni o'chirib, hisob-kitobni <b>0 dan</b> boshlamoqchimisiz?\n\n"
            f"❗️ <i>Ushbu oydagi barcha kirim va chiqimlaringiz o'chib ketadi. Ortga qaytarib bo'lmaydi!</i>"
        )
        confirm_btn = "⚠️ Ha, oyni tozalash (0 dan boshlash)"
        cancel_btn = "⬅️ Bekor qilish"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=confirm_btn, callback_data="do_reset_month")],
            [InlineKeyboardButton(text=cancel_btn, callback_data="hist_page_1")]
        ]
    )
    await callback.message.edit_text(warn_text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "do_reset_month")
async def execute_reset_month_callback(callback: CallbackQuery):
    """Joriy oy amallarini to'liq o'chirib 0 ga tushirish"""
    user_id = callback.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    is_ru = (user_lang == "ru")
    now = get_tashkent_now()
    month_name = MONTHS_RU.get(now.month, "") if is_ru else MONTHS_UZ.get(now.month, "")

    deleted_count = await db.delete_month_transactions(user_id, now.year, now.month)

    if is_ru:
        success_text = (
            f"✅ <b>Текущий месяц ({month_name} {now.year}) успешно очищен!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Удалено операций: <b>{deleted_count} шт.</b>\n"
            f"Ваш баланс и статистика за этот месяц сброшены в <b>0 сум</b>.\n\n"
            f"Теперь вы можете вести учёт заново с чистого листа! 🚀"
        )
    else:
        success_text = (
            f"✅ <b>Joriy oy ({now.year}-yil {month_name}) muvaffaqiyatli tozalandi!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"O'chirilgan amallar soni: <b>{deleted_count} ta</b>\n"
            f"Ushbu oy uchun balansingiz va statistikangiz <b>0 so'mga</b> tushirildi.\n\n"
            f"Endi hisob-kitobni 0 dan, toza varaqdan boshlashingiz mumkin! 🚀"
        )

    await callback.answer("✅ Tozalandi!" if not is_ru else "✅ Очищено!", show_alert=True)
    await callback.message.edit_text(success_text, reply_markup=None, parse_mode="HTML")
