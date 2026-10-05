from aiogram import Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from keyboards import get_main_keyboard, get_language_keyboard
from locales import t

router = Router()


@router.message(CommandStart(), StateFilter("*"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    user_lang = await db.get_user_language(user.id)

    # Foydalanuvchini bazaga qo'shish
    await db.add_user(
        user_id=user.id,
        full_name=user.full_name,
        username=user.username,
        language=user_lang
    )

    # Agar foydalanuvchi hali til tanlamagan bo'lsa
    if not user_lang:
        await message.answer(
            t("choose_lang", "uz"),
            reply_markup=get_language_keyboard(),
            parse_mode="HTML"
        )
        return

    # Tanlangan tildagi xush kelibsiz xabari
    welcome_text = t("welcome", user_lang, name=user.first_name)
    await message.answer(welcome_text, reply_markup=get_main_keyboard(user_lang), parse_mode="HTML")


@router.callback_query(F.data.startswith("set_lang_"))
async def process_language_choice(callback: CallbackQuery, state: FSMContext):
    """Foydalanuvchi tilni tanlaganda"""
    new_lang = "ru" if callback.data == "set_lang_ru" else "uz"
    user = callback.from_user

    await db.set_user_language(user.id, new_lang)
    await state.clear()

    try:
        await callback.message.delete()
    except Exception:
        pass

    welcome_text = t("welcome", new_lang, name=user.first_name)
    lang_note = t("lang_selected", new_lang)

    await callback.message.answer(
        f"{lang_note}\n\n{welcome_text}",
        reply_markup=get_main_keyboard(new_lang),
        parse_mode="HTML"
    )
    await callback.answer()


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

