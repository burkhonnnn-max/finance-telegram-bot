# -*- coding: utf-8 -*-
"""
Avto / Saqlangan tezkor amallar moduli (Quick Templates & One-Tap Actions)
Foydalanuvchi har kuni takrorlanadigan amallarini (masalan: Avtobus 2500 so'm, Non 4000 so'm)
bir marta saqlab qo'yadi va keyinchalik bitta tugmani bosish orqali hisobidan yechib oladi.
Yangi foydalanuvchida hech qanday avtomatik amal bo'lmaydi, o'zi xohlaganicha yaratadi.
"""

import re
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, Command

import database as db
from states import QuickTemplateState
from keyboards import (
    get_quick_templates_keyboard,
    get_quick_manage_keyboard,
    get_quick_cancel_keyboard,
    get_template_emoji,
    get_main_keyboard
)
from utils import format_money, parse_amount
from ai_voice import extract_number_from_text, parse_financial_intent

logger = logging.getLogger(__name__)
router = Router()


def detect_template_category(name: str, tr_type: str = "expense") -> str:
    """Nomi bo'yicha toifani aniqlash"""
    intent = parse_financial_intent(f"1000 {name}", forced_type=tr_type)
    cat = intent.get("category")
    if cat and "boshqa" not in cat.lower() and "другие" not in cat.lower():
        return cat

    low = name.lower()
    if any(w in low for w in ["avtobus", "metro", "taxi", "taksi", "benzin", "yo'l", "yol", "проезд", "автобус", "маршрутка", "газ"]):
        return "🚕 Transport & Yo'l"
    if any(w in low for w in ["non", "bozor", "ovqat", "osh", "go'sht", "gosht", "suv", "хлеб", "еда", "продукты", "обед"]):
        return "🍽 Oziq-ovqat"
    if any(w in low for w in ["kofe", "coffee", "choy", "kafe", "restoran", "кофе", "чай", "чайхана"]):
        return "☕️ Kafe & Restoran"
    if any(w in low for w in ["dori", "apteka", "аптека", "лекарства"]):
        return "💊 Salomatlik & Dori"
    if any(w in low for w in ["internet", "telefon", "paynet", "интернет"]):
        return "📱 Aloqa & Internet"
    if any(w in low for w in ["kommunal", "svet", "gaz", "ijara", "квартплата"]):
        return "🏠 Uy & Kommunal"

    return "📦 Boshqa chiqim" if tr_type == "expense" else "📦 Boshqa kirim"


# =========================================================================
# 1. ASOSIY MENYU: "⚡ Avto" TUGMASI BOSILGANDA
# =========================================================================

@router.message(F.text.in_({"⚡ Avto", "⚡ Авто", "Avto", "Авто"}), StateFilter("*"))
@router.message(Command("auto"), StateFilter("*"))
@router.message(Command("quick"), StateFilter("*"))
async def open_quick_actions(message: Message, state: FSMContext):
    """Avto menyusini ochish"""
    await state.clear()
    user_id = message.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    is_ru = (user_lang == "ru")

    if not await db.is_user_registered(user_id):
        msg = (
            "⚠️ <b>Iltimos, avval ro'yxatdan o'ting!</b>\n\n/start buyrug'ini bosing va shaxsiy hisobingizni yarating."
            if not is_ru else
            "⚠️ <b>Пожалуйста, сначала зарегистрируйтесь!</b>\n\nОтправьте команду /start для создания аккаунта."
        )
        await message.answer(msg, parse_mode="HTML")
        return

    templates = await db.get_quick_templates(user_id)

    if not templates:
        text = (
            "⚡ <b>Tezkor amallar (Avto)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Sizda hali saqlangan tezkor amallar yo'q.\n\n"
            "Har kuni takrorlanadigan to'lovlaringizni (masalan: <i>Avtobus 2 500 so'm, Non 4 000 so'm, Kofe 15 000 so'm</i>) "
            "bir marta saqlab qo'ying va har safar yozib o'tirmasdan, bitta tugmani bosish orqali balansingizdan yechib boring!\n\n"
            "Quyidagi tugma orqali birinchi amalingizni qo'shing 👇"
            if not is_ru else
            "⚡ <b>Быстрые операции (Авто)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "У вас пока нет сохранённых быстрых операций.\n\n"
            "Сохраните ваши ежедневные частые расходы (например: <i>Автобус 2 500 сум, Хлеб 4 000 сум, Кофе 15 000 сум</i>) "
            "и списывайте их в один клик без ввода суммы каждый раз!\n\n"
            "Нажмите кнопку ниже, чтобы создать первое действие 👇"
        )
    else:
        text = (
            "⚡ <b>Tezkor amallar (Avto)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Kerakli tugmani bosing — mablag' bir zumda balansingizdan yechiladi va hisobingizga yoziladi:\n"
            if not is_ru else
            "⚡ <b>Быстрые операции (Авто)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Нажмите нужную кнопку — сумма мгновенно спишется с вашего баланса:\n"
        )

    kb = get_quick_templates_keyboard(templates, lang=user_lang)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "quick_menu")
async def process_quick_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Callback orqali tezkor menyuga qaytish"""
    await state.clear()
    user_id = callback.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    is_ru = (user_lang == "ru")

    templates = await db.get_quick_templates(user_id)

    if not templates:
        text = (
            "⚡ <b>Tezkor amallar (Avto)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Sizda hali saqlangan tezkor amallar yo'q.\n\n"
            "Har kuni takrorlanadigan to'lovlaringizni (masalan: <i>Avtobus 2 500 so'm, Non 4 000 so'm, Kofe 15 000 so'm</i>) "
            "bir marta saqlab qo'ying va har safar bitta tugmani bosish orqali balansingizdan yeching!\n\n"
            "Quyidagi tugma orqali yangi amal qo'shing 👇"
            if not is_ru else
            "⚡ <b>Быстрые операции (Авто)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "У вас пока нет сохранённых быстрых операций.\n\n"
            "Нажмите кнопку ниже, чтобы добавить частое действие 👇"
        )
    else:
        text = (
            "⚡ <b>Tezkor amallar (Avto)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Kerakli tugmani bosing — mablag' bir zumda balansingizdan yechiladi va hisobingizga yoziladi:\n"
            if not is_ru else
            "⚡ <b>Быстрые операции (Авто)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Нажмите нужную кнопку — сумма мгновенно спишется с вашего баланса:\n"
        )

    kb = get_quick_templates_keyboard(templates, lang=user_lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "quick_close")
async def process_quick_close_callback(callback: CallbackQuery, state: FSMContext):
    """Menyuni yopish"""
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer()


# =========================================================================
# 2. BIR ZUMDA AMALNI BAJARISH (ONE-TAP EXECUTION)
# =========================================================================

@router.callback_query(F.data.startswith("quick_run_"))
async def execute_quick_action(callback: CallbackQuery, state: FSMContext):
    """Saqlangan amal tugmasi bosilganda darhol balansdan yechish"""
    await state.clear()
    user_id = callback.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    is_ru = (user_lang == "ru")

    try:
        tpl_id = int(callback.data.replace("quick_run_", ""))
    except ValueError:
        await callback.answer()
        return

    tpl = await db.get_quick_template(tpl_id, user_id)
    if not tpl:
        msg = "Amal topilmadi yoki o'chirilgan." if not is_ru else "Операция не найдена."
        await callback.answer(msg, show_alert=True)
        return

    amount = tpl["amount"]
    name = tpl["name"]
    tr_type = tpl["type"]
    category = tpl.get("category") or ("📦 Boshqa chiqim" if tr_type == "expense" else "📦 Boshqa kirim")

    # Bazaga tranzaksiya qo'shish
    tx_id = await db.add_transaction(
        user_id=user_id,
        tr_type=tr_type,
        amount=amount,
        category=category,
        comment=name
    )

    # Yangi balansni hisoblash
    bal_data = await db.get_balance(user_id)
    current_balance = bal_data["balance"]

    emoji = get_template_emoji(name, tr_type)
    amt_fmt = format_money(amount, lang=user_lang)
    bal_fmt = format_money(current_balance, lang=user_lang)

    # Toast bildirishnoma
    toast_msg = (
        f"✅ {name}: -{amt_fmt} yechildi!"
        if tr_type == "expense" else
        f"✅ {name}: +{amt_fmt} qo'shildi!"
    ) if not is_ru else (
        f"✅ {name}: -{amt_fmt} списано!"
        if tr_type == "expense" else
        f"✅ {name}: +{amt_fmt} добавлено!"
    )
    await callback.answer(toast_msg, show_alert=False)

    if not is_ru:
        card_text = (
            f"⚡ <b>Tezkor to'lov muvaffaqiyatli bajarildi!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔴 <b>Chiqim:</b> <b>-{amt_fmt}</b>\n"
            f"🏷 <b>Maqsad:</b> {emoji} <b>{name}</b>\n"
            f"📂 <b>Toifa:</b> {category}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Joriy balans:</b> <b>{bal_fmt}</b>\n\n"
            f"<i>Yana amal bajarish yoki bekor qilish uchun:</i>"
        ) if tr_type == "expense" else (
            f"⚡ <b>Tezkor kirim muvaffaqiyatli kiritildi!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🟢 <b>Kirim:</b> <b>+{amt_fmt}</b>\n"
            f"🏷 <b>Manba:</b> {emoji} <b>{name}</b>\n"
            f"📂 <b>Toifa:</b> {category}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Joriy balans:</b> <b>{bal_fmt}</b>\n\n"
            f"<i>Yana amal bajarish yoki bekor qilish uchun:</i>"
        )
        again_btn = "⚡ Yana amal bajarish"
        undo_btn = "↩️ Bekor qilish"
        close_btn = "❌ Yopish"
    else:
        card_text = (
            f"⚡ <b>Быстрое списание успешно выполнено!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔴 <b>Расход:</b> <b>-{amt_fmt}</b>\n"
            f"🏷 <b>Назначение:</b> {emoji} <b>{name}</b>\n"
            f"📂 <b>Категория:</b> {category}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Текущий баланс:</b> <b>{bal_fmt}</b>\n\n"
            f"<i>Для повторного действия или отмены:</i>"
        ) if tr_type == "expense" else (
            f"⚡ <b>Быстрый доход успешно добавлен!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🟢 <b>Доход:</b> <b>+{amt_fmt}</b>\n"
            f"🏷 <b>Источник:</b> {emoji} <b>{name}</b>\n"
            f"📂 <b>Категория:</b> {category}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Текущий баланс:</b> <b>{bal_fmt}</b>\n\n"
            f"<i>Для повторного действия или отмены:</i>"
        )
        again_btn = "⚡ Другие операции"
        undo_btn = "↩️ Отменить операцию"
        close_btn = "❌ Закрыть"

    action_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=again_btn, callback_data="quick_menu"),
                InlineKeyboardButton(text=undo_btn, callback_data=f"quick_undo_{tx_id}")
            ],
            [
                InlineKeyboardButton(text=close_btn, callback_data="quick_close")
            ]
        ]
    )

    try:
        await callback.message.edit_text(card_text, reply_markup=action_kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(card_text, reply_markup=action_kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("quick_undo_"))
async def execute_quick_undo(callback: CallbackQuery):
    """Tasodifan bosilgan amalni bekor qilish va bazadan o'chirish"""
    user_id = callback.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    is_ru = (user_lang == "ru")

    try:
        tx_id = int(callback.data.replace("quick_undo_", ""))
    except ValueError:
        await callback.answer()
        return

    deleted = await db.delete_transaction(tx_id, user_id)
    bal_data = await db.get_balance(user_id)
    bal_fmt = format_money(bal_data["balance"], lang=user_lang)

    if deleted:
        msg = "↩️ Amal bekor qilindi va o'chirildi." if not is_ru else "↩️ Операция успешно отменена."
        await callback.answer(msg, show_alert=True)
        text = (
            f"↩️ <b>Amal bekor qilindi va hisobingizdan o'chirildi!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Qayta tiklangan balans:</b> <b>{bal_fmt}</b>"
            if not is_ru else
            f"↩️ <b>Операция отменена и удалена из истории!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Восстановленный баланс:</b> <b>{bal_fmt}</b>"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⚡ Tezkor amallar" if not is_ru else "⚡ Быстрые операции", callback_data="quick_menu")],
                [InlineKeyboardButton(text="❌ Yopish" if not is_ru else "❌ Закрыть", callback_data="quick_close")]
            ]
        )
        try:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass
    else:
        await callback.answer("Amal topilmadi." if not is_ru else "Операция не найдена.", show_alert=True)


# =========================================================================
# 3. SAQLANGAN AMALLARNI BOSHQARISH VA O'CHIRISH
# =========================================================================

@router.callback_query(F.data == "quick_manage")
async def open_quick_manage(callback: CallbackQuery, state: FSMContext):
    """Amallarni o'chirish ro'yxatini ochish"""
    await state.clear()
    user_id = callback.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    is_ru = (user_lang == "ru")

    templates = await db.get_quick_templates(user_id)

    if not templates:
        await callback.answer("Sizda amallar yo'q." if not is_ru else "У вас нет операций.", show_alert=True)
        return

    text = (
        "⚙️ <b>Keraksiz tezkor amalni o'chirish:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "O'chirmoqchi bo'lgan amalingiz ustiga bosing 👇"
        if not is_ru else
        "⚙️ <b>Удаление быстрых операций:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Нажмите на операцию, которую хотите удалить 👇"
    )
    kb = get_quick_manage_keyboard(templates, lang=user_lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("quick_del_"))
async def delete_quick_action(callback: CallbackQuery):
    """Aynan bitta saqlangan amalni o'chirish"""
    user_id = callback.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    is_ru = (user_lang == "ru")

    try:
        tpl_id = int(callback.data.replace("quick_del_", ""))
    except ValueError:
        await callback.answer()
        return

    await db.delete_quick_template(tpl_id, user_id)
    await callback.answer("✅ O'chirildi!" if not is_ru else "✅ Удалено!", show_alert=False)

    templates = await db.get_quick_templates(user_id)
    if not templates:
        text = (
            "✅ <b>Barcha amallar o'chirildi.</b>\n\n"
            "Yangi tezkor amal qo'shishingiz mumkin 👇"
            if not is_ru else
            "✅ <b>Все операции удалены.</b>\n\n"
            "Вы можете добавить новую операцию 👇"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Yangi qo'shish" if not is_ru else "➕ Добавить", callback_data="quick_add_new")],
                [InlineKeyboardButton(text="⬅️ Ortga" if not is_ru else "⬅️ Назад", callback_data="quick_menu")]
            ]
        )
    else:
        text = (
            "⚙️ <b>Keraksiz tezkor amalni o'chirish:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "O'chirmoqchi bo'lgan amalingiz ustiga bosing 👇"
            if not is_ru else
            "⚙️ <b>Удаление быстрых операций:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Нажмите на операцию, которую хотите удалить 👇"
        )
        kb = get_quick_manage_keyboard(templates, lang=user_lang)

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass


# =========================================================================
# 4. YANGI TEZKOR AMAL QO'SHISH (FSM FLOW)
# =========================================================================

@router.callback_query(F.data == "quick_add_new")
async def start_quick_add(callback: CallbackQuery, state: FSMContext):
    """Yangi tezkor amal qo'shish jarayonini boshlash"""
    user_id = callback.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    is_ru = (user_lang == "ru")

    await state.set_state(QuickTemplateState.waiting_title_or_quick)

    text = (
        "➕ <b>Yangi tezkor amal qo'shish</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Tezkor amalning <b>nomi va summasini</b> yozib yuboring:\n\n"
        "💡 <b>Qulay usul:</b> Nomi va summasini bitta xabarda yozing:\n"
        "• <code>Avtobus 2500</code>\n"
        "• <code>Non 4000</code>\n"
        "• <code>Metro 2000</code>\n"
        "• <code>Kofe 15000</code>\n\n"
        "Yoki faqat nomini yozing (masalan: <i>Avtobus</i>), summasini keyingi qadamda so'rayman."
        if not is_ru else
        "➕ <b>Добавление быстрой операции</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Отправьте <b>название и сумму</b> быстрой операции:\n\n"
        "💡 <b>Удобный способ:</b> Напишите в одном сообщении:\n"
        "• <code>Автобус 2500</code>\n"
        "• <code>Хлеб 4000</code>\n"
        "• <code>Метро 2000</code>\n"
        "• <code>Кофе 15000</code>\n\n"
        "Или отправьте только название (например: <i>Автобус</i>), сумму запрошу следующим шагом."
    )
    kb = get_quick_cancel_keyboard(lang=user_lang)
    await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "quick_cancel_add")
async def cancel_quick_add(callback: CallbackQuery, state: FSMContext):
    """Qo'shishni bekor qilish"""
    await state.clear()
    user_id = callback.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    is_ru = (user_lang == "ru")

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.answer("Bekor qilindi" if not is_ru else "Отменено", show_alert=False)
    # Asosiy menyuni qayta ko'rsatamiz
    templates = await db.get_quick_templates(user_id)
    kb = get_quick_templates_keyboard(templates, lang=user_lang)
    menu_title = (
        "⚡ <b>Tezkor amallar (Avto)</b>"
        if not is_ru else
        "⚡ <b>Быстрые операции (Авто)</b>"
    )
    await callback.message.answer(menu_title, reply_markup=kb, parse_mode="HTML")


@router.message(QuickTemplateState.waiting_title_or_quick, F.text)
async def process_quick_title_or_both(message: Message, state: FSMContext):
    """Nomi va/yoki summasini qabul qilish"""
    raw_text = message.text.strip()
    user_id = message.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    is_ru = (user_lang == "ru")

    if raw_text in ["❌ Bekor qilish", "❌ Отмена", "/cancel"]:
        await state.clear()
        cancel_msg = "Bekor qilindi." if not is_ru else "Отменено."
        await message.answer(cancel_msg, reply_markup=get_main_keyboard(user_lang))
        return

    # 1-holat: Matndan son/summani qidiramiz
    amount = extract_number_from_text(raw_text)

    if amount and amount > 0:
        # Foydalanuvchi "Avtobus 2500" yoki "Non 4000" kabi bitta xabarda yozgan!
        # Nomdan raqamlarni olib tashlaymiz
        name_clean = re.sub(r'[\d\.,\s]+(ming|so\'m|som|сум|тыс|k)?', ' ', raw_text, flags=re.IGNORECASE).strip()
        if not name_clean or len(name_clean) < 2:
            name_clean = "Tezkor to'lov" if not is_ru else "Быстрый платёж"
        else:
            name_clean = name_clean.capitalize()

        category = detect_template_category(name_clean, tr_type="expense")

        # Bazaga qo'shish
        await db.add_quick_template(
            user_id=user_id,
            name=name_clean,
            amount=amount,
            tr_type="expense",
            category=category
        )
        await state.clear()

        emoji = get_template_emoji(name_clean, "expense")
        amt_fmt = format_money(amount, lang=user_lang)

        success_text = (
            f"🎉 <b>Yangi tezkor amal muvaffaqiyatli saqlandi!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷 <b>Nomi:</b> {emoji} <b>{name_clean}</b>\n"
            f"💵 <b>Summasi:</b> <b>{amt_fmt}</b>\n"
            f"📂 <b>Toifasi:</b> {category}\n\n"
            f"Endi <b>⚡ Avto</b> tugmasini bosganingizda ushbu amal chiqadi va bitta bosishda hisobingizdan yechiladi! 🚀"
            if not is_ru else
            f"🎉 <b>Быстрая операция успешно сохранена!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷 <b>Название:</b> {emoji} <b>{name_clean}</b>\n"
            f"💵 <b>Сумма:</b> <b>{amt_fmt}</b>\n"
            f"📂 <b>Категория:</b> {category}\n\n"
            f"Теперь по нажатию кнопки <b>⚡ Авто</b> операция будет списываться в один клик! 🚀"
        )
        view_btn = "⚡ Avto menyusini ochish" if not is_ru else "⚡ Открыть меню Авто"
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=view_btn, callback_data="quick_menu")]
            ]
        )
        await message.answer(success_text, reply_markup=kb, parse_mode="HTML")

    else:
        # 2-holat: Faqat nom yozilgan (masalan: "Avtobus" yoki "Non")
        name = raw_text.capitalize()
        await state.update_data(tpl_name=name)
        await state.set_state(QuickTemplateState.waiting_amount)

        ask_amt_text = (
            f"Rahmat! <b>{name}</b> uchun qancha summa yechilsin?\n\n"
            f"<i>(Masalan: 2500 yoki 4000)</i>"
            if not is_ru else
            f"Отлично! Какую сумму списывать для <b>{name}</b>?\n\n"
            f"<i>(Например: 2500 или 4000)</i>"
        )
        kb = get_quick_cancel_keyboard(lang=user_lang)
        await message.answer(ask_amt_text, reply_markup=kb, parse_mode="HTML")


@router.message(QuickTemplateState.waiting_amount, F.text)
async def process_quick_amount(message: Message, state: FSMContext):
    """Faqat summani qabul qilish va yakunlash"""
    raw_text = message.text.strip()
    user_id = message.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    is_ru = (user_lang == "ru")

    if raw_text in ["❌ Bekor qilish", "❌ Отмена", "/cancel"]:
        await state.clear()
        cancel_msg = "Bekor qilindi." if not is_ru else "Отменено."
        await message.answer(cancel_msg, reply_markup=get_main_keyboard(user_lang))
        return

    amount = extract_number_from_text(raw_text)
    if not amount or amount <= 0:
        err = (
            "⚠️ Iltimos, summani to'g'ri kiriting:\n<i>(Masalan: 2500 yoki 15000)</i>"
            if not is_ru else
            "⚠️ Пожалуйста, введите корректную сумму:\n<i>(Например: 2500 или 15000)</i>"
        )
        await message.answer(err, parse_mode="HTML")
        return

    data = await state.get_data()
    name = data.get("tpl_name") or ("Tezkor chiqim" if not is_ru else "Быстрый расход")
    category = detect_template_category(name, tr_type="expense")

    # Bazaga qo'shish
    await db.add_quick_template(
        user_id=user_id,
        name=name,
        amount=amount,
        tr_type="expense",
        category=category
    )
    await state.clear()

    emoji = get_template_emoji(name, "expense")
    amt_fmt = format_money(amount, lang=user_lang)

    success_text = (
        f"🎉 <b>Yangi tezkor amal muvaffaqiyatli saqlandi!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷 <b>Nomi:</b> {emoji} <b>{name}</b>\n"
        f"💵 <b>Summasi:</b> <b>{amt_fmt}</b>\n"
        f"📂 <b>Toifasi:</b> {category}\n\n"
        f"Endi <b>⚡ Avto</b> tugmasini bosganingizda ushbu amal chiqadi va bitta bosishda hisobingizdan yechiladi! 🚀"
        if not is_ru else
        f"🎉 <b>Быстрая операция успешно сохранена!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷 <b>Название:</b> {emoji} <b>{name}</b>\n"
        f"💵 <b>Сумма:</b> <b>{amt_fmt}</b>\n"
        f"📂 <b>Категория:</b> {category}\n\n"
        f"Теперь по нажатию кнопки <b>⚡ Авто</b> операция будет списываться в один клик! 🚀"
    )
    view_btn = "⚡ Avto menyusini ochish" if not is_ru else "⚡ Открыть меню Авто"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=view_btn, callback_data="quick_menu")]
        ]
    )
    await message.answer(success_text, reply_markup=kb, parse_mode="HTML")
