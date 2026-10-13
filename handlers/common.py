import re
from aiogram import Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

import database as db
from keyboards import get_main_keyboard, get_language_keyboard, get_phone_keyboard
from states import RegistrationState
from locales import t

router = Router()


@router.message(CommandStart(), StateFilter("*"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    user_data = await db.get_user(user.id)

    # Agar foydalanuvchi allaqachon to'liq ro'yxatdan o'tgan bo'lsa
    if user_data and user_data.get("is_registered") and user_data.get("phone_number"):
        user_lang = user_data.get("language") or "uz"
        name = user_data.get("full_name") or user.first_name
        welcome_text = t("welcome", user_lang, name=name)
        await message.answer(welcome_text, reply_markup=get_main_keyboard(user_lang), parse_mode="HTML")
        return

    # Yangi foydalanuvchi: hali til tanlanmagan bo'lsa
    user_lang = await db.get_user_language(user.id)
    if not user_lang:
        await message.answer(
            t("choose_lang", "uz"),
            reply_markup=get_language_keyboard(),
            parse_mode="HTML"
        )
        return

    # Til tanlangan, lekin ro'yxatdan o'tmagan bo'lsa
    await start_registration_name(message, state, user_lang)


async def start_registration_name(message: Message, state: FSMContext, lang: str):
    """Ro'yxatdan o'tish: Ism va familiyani so'rash"""
    await state.set_state(RegistrationState.waiting_full_name)
    is_ru = (lang == "ru")
    prompt = (
        "👋 <b>Xush kelibsiz!</b>\n\n"
        "Botingizdan shaxsiy hisob ochish uchun, iltimos, <b>ism va familiyangizni</b> kiriting:\n"
        "<i>(Masalan: Alisher Valiyev)</i>"
        if not is_ru else
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Для создания личного аккаунта, пожалуйста, введите ваши <b>имя и фамилию</b>:\n"
        "<i>(Например: Алишер Валиев)</i>"
    )
    await message.answer(prompt, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")


@router.callback_query(F.data.startswith("set_lang_"))
async def process_language_choice(callback: CallbackQuery, state: FSMContext):
    """Foydalanuvchi tilni tanlaganda"""
    new_lang = "ru" if callback.data == "set_lang_ru" else "uz"
    user = callback.from_user

    await db.set_user_language(user.id, new_lang)
    user_data = await db.get_user(user.id)

    try:
        await callback.message.delete()
    except Exception:
        pass

    # Agar allaqachon ro'yxatdan o'tgan bo'lsa (shunchaki tilni o'zgartirgan)
    if user_data and user_data.get("is_registered") and user_data.get("phone_number"):
        await state.clear()
        name = user_data.get("full_name") or user.first_name
        welcome_text = t("welcome", new_lang, name=name)
        lang_note = t("lang_selected", new_lang)
        await callback.message.answer(
            f"{lang_note}\n\n{welcome_text}",
            reply_markup=get_main_keyboard(new_lang),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    # Yangi foydalanuvchi: Ism-familiyani kiritishga yo'naltirish
    await start_registration_name(callback.message, state, new_lang)
    await callback.answer()


@router.message(RegistrationState.waiting_full_name, F.text)
async def process_full_name(message: Message, state: FSMContext):
    """Ism va familiyani qabul qilish"""
    full_name = message.text.strip()
    user_lang = (await db.get_user_language(message.from_user.id)) or "uz"
    is_ru = (user_lang == "ru")

    if full_name in ["❌ Bekor qilish", "❌ Отмена", "/cancel"]:
        await state.clear()
        await message.answer(t("cancelled", user_lang), reply_markup=ReplyKeyboardRemove())
        return

    if len(full_name) < 2 or full_name.startswith("/"):
        err = (
            "Iltimos, ism va familiyangizni to'liqroq yozing:\n<i>(Masalan: Alisher Valiyev)</i>"
            if not is_ru else
            "Пожалуйста, введите имя и фамилию корректно:\n<i>(Например: Алишер Валиев)</i>"
        )
        await message.answer(err, parse_mode="HTML")
        return

    await state.update_data(full_name=full_name)
    await state.set_state(RegistrationState.waiting_phone)

    phone_prompt = (
        f"Rahmat, <b>{full_name}</b>! 🤝\n\n"
        f"Endi hisobingizni faollashtirish uchun <b>telefon raqamingizni</b> yuboring.\n\n"
        f"Quyidagi <b>«📱 Telefon raqamni ulashish»</b> tugmasini bosing yoki raqamingizni qo'lda yozib yuboring:\n"
        f"<i>(Masalan: +998901234567)</i>"
        if not is_ru else
        f"Спасибо, <b>{full_name}</b>! 🤝\n\n"
        f"Теперь для активации аккаунта отправьте ваш <b>номер телефона</b>.\n\n"
        f"Нажмите кнопку <b>«📱 Поделиться контактом»</b> ниже или введите номер вручную:\n"
        f"<i>(Например: +998901234567)</i>"
    )
    await message.answer(
        phone_prompt,
        reply_markup=get_phone_keyboard(user_lang),
        parse_mode="HTML"
    )


@router.message(RegistrationState.waiting_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    """Telefon raqamini Telegram Contact orqali qabul qilish"""
    contact = message.contact
    phone = contact.phone_number.strip()
    if not phone.startswith("+"):
        phone = f"+{phone}"
    await complete_registration(message, state, phone)


@router.message(RegistrationState.waiting_phone, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    """Telefon raqamini qo'lda yozilgan holda qabul qilish"""
    user_lang = (await db.get_user_language(message.from_user.id)) or "uz"
    is_ru = (user_lang == "ru")
    text = message.text.strip()

    if text in ["❌ Bekor qilish", "❌ Отмена", "/cancel"]:
        await state.clear()
        await message.answer(t("cancelled", user_lang), reply_markup=ReplyKeyboardRemove())
        return

    clean_digits = re.sub(r"[^\d]", "", text)
    if len(clean_digits) < 7:
        err = (
            "⚠️ Noto'g'ri telefon raqami kiritildi.\n\n"
            "Iltimos, pastdagi <b>«📱 Telefon raqamni ulashish»</b> tugmasini bosing yoki raqamingizni to'liq kiriting:\n"
            "<i>(Masalan: +998901234567)</i>"
            if not is_ru else
            "⚠️ Неверный формат номера телефона.\n\n"
            "Пожалуйста, нажмите кнопку <b>«📱 Поделиться контактом»</b> ниже или введите номер вручную:\n"
            "<i>(Например: +998901234567)</i>"
        )
        await message.answer(err, reply_markup=get_phone_keyboard(user_lang), parse_mode="HTML")
        return

    phone = f"+{clean_digits}"
    await complete_registration(message, state, phone)


async def complete_registration(message: Message, state: FSMContext, phone: str):
    """Ro'yxatdan o'tishni yakunlash va shaxsiy hisob ochish"""
    data = await state.get_data()
    full_name = data.get("full_name") or message.from_user.full_name or "Foydalanuvchi"
    user_lang = (await db.get_user_language(message.from_user.id)) or "uz"
    is_ru = (user_lang == "ru")

    # Bazada ro'yxatdan o'tkazish
    await db.register_user(
        user_id=message.from_user.id,
        full_name=full_name,
        phone_number=phone,
        language=user_lang,
        username=message.from_user.username
    )
    await state.clear()

    if is_ru:
        success_text = (
            f"🎉 <b>Поздравляем, {full_name}!</b>\n"
            f"Ваш личный аккаунт успешно создан и активирован! 🚀\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Имя:</b> {full_name}\n"
            f"📱 <b>Телефон:</b> {phone}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Теперь все ваши доходы, расходы и статистика будут сохраняться в вашем персональном кабинете.\n\n"
            f"<i>Выберите действие в меню ниже или отправьте голосовое сообщение!</i> 👇"
        )
    else:
        success_text = (
            f"🎉 <b>Tabriklaymiz, {full_name}!</b>\n"
            f"Shaxsiy hisobingiz muvaffaqiyatli yaratildi va faollashtirildi! 🚀\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Foydalanuvchi:</b> {full_name}\n"
            f"📱 <b>Telefon:</b> {phone}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Endi barcha daromad, xarajat va hisobotlaringiz faqat sizning shaxsiy hisobingizda xavfsiz saqlanadi.\n\n"
            f"<i>Pastdagi menyudan kerakli bo'limni tanlang yoki ovozli xabar yuboring!</i> 👇"
        )

    await message.answer(success_text, reply_markup=get_main_keyboard(user_lang), parse_mode="HTML")


@router.message(F.text.in_({"🌐 Til / Язык", "/lang", "/language"}), StateFilter("*"))
@router.message(Command("language"), StateFilter("*"))
@router.message(Command("lang"), StateFilter("*"))
async def cmd_change_language(message: Message, state: FSMContext):
    """Tilni o'zgartirish tugmasi (har qanday holatda darhol ishlaydi)"""
    await state.clear()
    user_lang = (await db.get_user_language(message.from_user.id)) or "uz"
    await message.answer(
        t("choose_lang", user_lang),
        reply_markup=get_language_keyboard(),
        parse_mode="HTML"
    )


@router.message(Command("restart"), StateFilter("*"))
async def cmd_restart(message: Message, state: FSMContext):
    """Bot holatini tozalash va qayta ishga tushirish buyrug'i"""
    await state.clear()
    user_lang = (await db.get_user_language(message.from_user.id)) or "uz"

    restart_msg = (
        "🔄 <b>Бот успешно перезапущен!</b>\n\nМеню обновлено, можете продолжать работу 👇"
        if user_lang == "ru"
        else "🔄 <b>Bot muvaffaqiyatli qayta ishga tushirildi!</b>\n\nMenyu qayta yuklandi, ishlashda davom etishingiz mumkin 👇"
    )

    await message.answer(
        restart_msg,
        reply_markup=get_main_keyboard(user_lang),
        parse_mode="HTML"
    )


@router.message(F.text.in_({"ℹ️ Qanday ishlatiladi?", "ℹ️ Yordam", "ℹ️ Помощь"}), StateFilter("*"))
@router.message(Command("help"), StateFilter("*"))
async def cmd_help(message: Message, state: FSMContext):
    await state.clear()
    user_lang = (await db.get_user_language(message.from_user.id)) or "uz"
    help_text = t("help_text", user_lang)
    await message.answer(help_text, reply_markup=get_main_keyboard(user_lang), parse_mode="HTML")


@router.message(F.text.in_({"❌ Bekor qilish", "❌ Отмена"}), StateFilter("*"))
@router.message(Command("cancel"), StateFilter("*"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    user_lang = (await db.get_user_language(message.from_user.id)) or "uz"
    await message.answer(t("cancelled", user_lang), reply_markup=get_main_keyboard(user_lang))


@router.callback_query(F.data == "cancel_action")
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_lang = (await db.get_user_language(callback.from_user.id)) or "uz"
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(t("cancelled", user_lang), reply_markup=get_main_keyboard(user_lang))
    await callback.answer()


@router.message(Command("backup"), StateFilter("*"))
async def cmd_backup(message: Message, state: FSMContext):
    await state.clear()
    import os
    from aiogram.types import FSInputFile
    from config import DB_PATH

    if os.path.exists(DB_PATH):
        doc = FSInputFile(DB_PATH, filename="finance_bot.db")
        await message.answer_document(
            doc,
            caption="💾 <b>Ma'lumotlar bazasining zaxira nusxasi (Backup)</b>",
            parse_mode="HTML"
        )
    else:
        await message.answer("Baza fayli topilmadi.")

