import io
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import database as db
from ai_voice import process_voice_audio
from utils import format_money
from keyboards import get_main_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.voice | F.audio)
async def handle_voice_message(message: Message, state: FSMContext):
    """Foydalanuvchining ovozli xabarini qabul qilish va AI orqali tahlil qilish"""
    # Foydalanuvchi biror boshqa holatda bo'lsa tozalaymiz
    await state.clear()

    voice = message.voice or message.audio
    if not voice:
        return

    # Foydalanuvchiga jarayon ketayotganini bildirish
    processing_msg = await message.answer("🎙 <i>Ovozingiz eshitilmoqda va tahlil qilinmoqda...</i>", parse_mode="HTML")

    try:
        # Ovoz faylini xotiraga yuklab olish
        file = await message.bot.get_file(voice.file_id)
        audio_stream = io.BytesIO()
        await message.bot.download_file(file.file_path, destination=audio_stream)
        audio_bytes = audio_stream.getvalue()

        # Gemini AI orqali ovozni tahlil qilish
        result = await process_voice_audio(audio_bytes)

        if not result["success"]:
            if result.get("error_type") == "no_api_key":
                help_text = (
                    "🎙 <b>Ovozli xabarlarni tushunish funksiyasi tayyor!</b>\n\n"
                    "Lekin botda <b>GEMINI_API_KEY</b> kaliti hali kiritilmagan.\n\n"
                    "Uni olish juda oson va mutlaqo bepul (1 daqiqa):\n"
                    "1. <a href='https://aistudio.google.com/apikey'>aistudio.google.com/apikey</a> saytiga kiring;\n"
                    "2. <b>'Create API key'</b> tugmasini bosing;\n"
                    "3. Chiqqan kalitni Render.com dagi <b>Environment Variables</b> bo'limiga <code>GEMINI_API_KEY</code> nomi bilan qo'shing.\n\n"
                    "Shundan so'ng bot ovozingizni mukammal tushunadi!"
                )
                await processing_msg.edit_text(help_text, parse_mode="HTML", disable_web_page_preview=True)
                return
            else:
                await processing_msg.edit_text(
                    "⚠️ Ovozni tahlil qilishda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring yoki matn ko'rinishida yozing."
                )
                return

        data = result["data"]

        # Agar moliyaviy ma'lumot bo'lmasa
        if not data.get("is_finance", True) or not data.get("amount"):
            transcript = data.get("transcript", "")
            transcript_text = f"«<i>{transcript}</i>»\n\n" if transcript else ""
            await processing_msg.edit_text(
                f"🎙 <b>Eshitildi:</b> {transcript_text}"
                f"⚠️ Ovozdan kirim yoki chiqim summasi aniqlanmadi.\n\n"
                f"Iltimos, aniqroq ayting, masalan:\n"
                f"• <i>'Tushlikka 30 ming sarfladim'</i>\n"
                f"• <i>'Taksiga 15 ming ketdi'</i>\n"
                f"• <i>'Oylik 1 million tushdi'</i>",
                parse_mode="HTML"
            )
            return

        tr_type = data.get("type", "expense")
        amount = float(data.get("amount", 0))
        category = data.get("category", "📦 Boshqa chiqim" if tr_type == "expense" else "📦 Boshqa kirim")
        comment = data.get("comment", "")
        transcript = data.get("transcript", "")

        # Bazaga saqlash
        user_id = message.from_user.id
        await db.add_user(user_id=user_id, full_name=message.from_user.full_name, username=message.from_user.username)
        await db.add_transaction(
            user_id=user_id,
            tr_type=tr_type,
            amount=amount,
            category=category,
            comment=comment
        )

        balance_info = await db.get_balance(user_id)

        sign = "🟢 +" if tr_type == "income" else "🔴 -"
        type_label = "Kirim" if tr_type == "income" else "Chiqim"

        response = (
            f"🎙 <b>Eshitildi:</b> «<i>{transcript}</i>»\n\n"
            f"✅ <b>{type_label} muvaffaqiyatli saqlandi!</b>\n\n"
            f"💵 <b>Summa:</b> {sign}{format_money(amount)}\n"
            f"🏷 <b>Toifa:</b> {category}\n"
        )
        if comment:
            response += f"📝 <b>Izoh:</b> {comment}\n"
        
        response += f"\n💰 <b>Joriy sof balans:</b> {format_money(balance_info['balance'])}"

        await processing_msg.edit_text(response, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Voice handler exception: {e}")
        await processing_msg.edit_text(
            "⚠️ Ovozli xabarni qabul qilishda texnik xatolik yuz berdi.",
            parse_mode="HTML"
        )
