from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from keyboards import get_main_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    await db.add_user(
        user_id=user.id,
        full_name=user.full_name,
        username=user.username
    )

    welcome_text = (
        f"Assalomu alaykum, <b>{user.first_name}</b>! 💰\n\n"
        f"Men sizning shaxsiy <b>Kirim-Chiqim va Moliya hisobchi botingizman</b>.\n\n"
        f"Bu bot orqali siz:\n"
        f"• Kundalik harajat va daromadlaringizni yozib borishingiz;\n"
        f"• Qayerga qancha pul ketayotganini aniq bilishingiz;\n"
        f"• Kunlik, haftalik va oylik hisobotlarni ko'rishingiz;\n"
        f"• Hamyoningizdagi sof balansni doimiy kuzatib borishingiz mumkin!\n\n"
        f"Pastdagi menyu tugmalari orqali ishlashni boshlashingiz mumkin 👇"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard(), parse_mode="HTML")


@router.message(Command("restart"))
async def cmd_restart(message: Message, state: FSMContext):
    """Bot holatini tozalash va qayta ishga tushirish buyrug'i"""
    await state.clear()
    await message.answer(
        "🔄 <b>Bot muvaffaqiyatli qayta ishga tushirildi!</b>\n\n"
        "Barcha joriy amallar yangilandi va menyu qayta yuklandi. Marhamat, ishlashda davom etishingiz mumkin 👇",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )



@router.message(F.text == "ℹ️ Qanday ishlatiladi?")
@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "💡 <b>Botdan foydalanish bo'yicha qo'llanma</b>\n\n"
        "<b>1. Tugmalar orqali kiritish:</b>\n"
        "• <b>➕ Kirim qo'shish</b> yoki <b>➖ Chiqim qo'shish</b> tugmasini bosing;\n"
        "• Summani kiriting (masalan: <code>50000</code> yoki <code>50k</code>);\n"
        "• Toifani tanlang (Oziq-ovqat, Transport va h.k.);\n"
        "• Izoh yozing yoki 'O'tkazib yuborish'ni bosing.\n\n"
        "<b>2. Tezkor yozuv usuli (Eng qulayi!):</b>\n"
        "Hech qanday tugma bosmasdan to'g'ridan-to'g'ri xabar yuborishingiz mumkin:\n"
        "• <code>-15000 tushlik</code> (15 000 so'm ovqat chiqimi)\n"
        "• <code>-20k taxi</code> (20 000 so'm transport chiqimi)\n"
        "• <code>+500000 oylik</code> (500 000 so'm maosh kirimi)\n"
        "• <code>+100k frilans</code> (100 000 so'm daromad)\n\n"
        "<b>3. Hisobotlar va Balans:</b>\n"
        "• <b>💰 Mening balansim</b> — joriy sof balansingiz;\n"
        "• <b>📊 Statistika & Hisobot</b> — bugungi, haftalik va oylik harajatlar diagrammasi;\n"
        "• <b>🕒 Oxirgi amallar</b> — oxirgi yozuvlar va xato yozilganini o'chirish."
    )
    await message.answer(help_text, reply_markup=get_main_keyboard(), parse_mode="HTML")


@router.message(F.text == "❌ Bekor qilish")
@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Barcha amallar bekor qilindi.", reply_markup=get_main_keyboard())


@router.callback_query(F.data == "cancel_action")
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Amal bekor qilindi.", reply_markup=get_main_keyboard())
    await callback.answer()
