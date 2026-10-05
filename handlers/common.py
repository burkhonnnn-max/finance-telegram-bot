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
        f"✨ <b>Asosiy imkoniyatlar:</b>\n"
        f"• <b>💰 Kirim</b> va <b>💳 Chiqim</b> tugmalari orqali xarajat va daromadlarni kiritish;\n"
        f"• 🎙 <b>Ovozli xabar</b> yuborish — AI uni eshitib, summa va maqsadini aniqlaydi;\n"
        f"• <b>✅ Done</b> (Tasdiqlash) va <b>✏️ Fix</b> (To'g'rilash) tugmalari orqali ma'lumotlarni tekshirib saqlash;\n"
        f"• <b>📊 Statistika</b> va <b>💰 Balans</b>ni bir zumda ko'rish!\n\n"
        f"Quyidagi menyu tugmalaridan birini tanlang 👇"
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


@router.message(F.text.in_({"ℹ️ Qanday ishlatiladi?", "ℹ️ Yordam"}))
@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "💡 <b>Botdan foydalanish bo'yicha qo'llanma</b>\n\n"
        "<b>1. Kirim yoki Chiqim kiritish:</b>\n"
        "• Pastdagi <b>💰 Kirim</b> yoki <b>💳 Chiqim</b> tugmasini bosing;\n"
        "• Summa va nima uchunligini yozing (masalan: <code>25 000 tushlik</code>) yoki 🎙 <b>ovozli xabar</b> yuboring;\n"
        "• Bot ma'lumotni tahlil qilib sizga ko'rsatadi;\n"
        "• Agar to'g'ri bo'lsa <b>✅ Done</b> tugmasini bosing;\n"
        "• Agar hatolik bo'lsa <b>✏️ Fix</b> tugmasini bosib, summa, tur yoki izohni to'g'rilang!\n\n"
        "<b>2. Tezkor yozuv usuli:</b>\n"
        "To'g'ridan-to'g'ri xabar yuborishingiz mumkin:\n"
        "• <code>-15000 tushlik</code> (15 000 so'm ovqat chiqimi)\n"
        "• <code>-20k taxi</code> (20 000 so'm transport chiqimi)\n"
        "• <code>+500000 oylik</code> (500 000 so'm maosh kirimi)\n\n"
        "<b>3. Ovozli xabar:</b>\n"
        "Ovozli xabarda nima uchun va qancha ketganini ayting (masalan: <i>'Tushlikka 35 ming ketdi'</i>).\n"
        "AI uni tahlil qilib, tasdiqlash uchun chiqaradi!\n\n"
        "<b>4. Hisobotlar va Balans:</b>\n"
        "• <b>💰 Mening balansim</b> — joriy sof balansingiz;\n"
        "• <b>📊 Statistika & Hisobot</b> — bugungi, haftalik va oylik hisobotlar;\n"
        "• <b>🕒 Oxirgi amallar</b> — oxirgi yozuvlar va o'chirish."
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
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("Amal bekor qilindi.", reply_markup=get_main_keyboard())
    await callback.answer()
