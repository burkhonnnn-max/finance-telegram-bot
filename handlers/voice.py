import io
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from ai_voice import process_voice_audio, parse_financial_intent
from utils import format_money, parse_amount
from states import PendingEditState
from keyboards import (
    get_main_keyboard,
    get_confirm_keyboard,
    get_fix_keyboard,
    get_type_keyboard,
)
import pending_manager as pm

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.voice | F.audio)
async def handle_voice_message(message: Message, state: FSMContext):
    """Foydalanuvchining ovozli xabarini qabul qilish va AI orqali tahlil qilish"""
    # Agar foydalanuvchi oldin Kirim yoki Chiqim tugmasini tanlagan bo'lsa
    state_data = await state.get_data()
    preselected_type = state_data.get("tr_type")
    await state.clear()

    voice = message.voice or message.audio
    if not voice:
        return

    # Jarayon ketayotganini bildirish
    processing_msg = await message.answer(
        "🎙 <i>Ovozingiz eshitilmoqda va tahlil qilinmoqda...</i>", parse_mode="HTML"
    )

    try:
        # Audio faylni yuklab olish
        file = await message.bot.get_file(voice.file_id)
        audio_stream = io.BytesIO()
        await message.bot.download_file(file.file_path, destination=audio_stream)
        audio_bytes = audio_stream.getvalue()

        # Ovozni tahlil qilish
        result = await process_voice_audio(audio_bytes, forced_type=preselected_type)

        if not result.get("success"):
            if result.get("error_type") == "no_speech":
                await processing_msg.edit_text(
                    "🎙 <b>Ovoz aniq eshitilmadi.</b>\n\n"
                    "Iltimos, mikrofonga yaqinroq gapiring yoki xabarni yozma shaklda yuboring "
                    "(masalan: <i>'25 000 tushlik'</i>).",
                    parse_mode="HTML"
                )
                return
            else:
                err_text = result.get("message", "Noma'lum xatolik")
                await processing_msg.edit_text(
                    f"⚠️ Ovozni tahlil qilishda xatolik yuz berdi:\n<code>{err_text[:200]}</code>",
                    parse_mode="HTML"
                )
                return

        data = result["data"]

        # Agar summa aniqlanmagan bo'lsa
        if not data.get("is_finance", True) or not data.get("amount"):
            transcript = data.get("transcript", "")
            transcript_text = f"«<i>{transcript}</i>»\n\n" if transcript else ""
            await processing_msg.edit_text(
                f"🎙 <b>Eshitildi:</b> {transcript_text}"
                f"⚠️ Ovozdan summa aniqlanmadi.\n\n"
                f"Iltimos, summani ham aytib o'ting, masalan:\n"
                f"• <i>'Tushlikka 30 ming sarfladim'</i>\n"
                f"• <i>'Taksiga 15 ming ketdi'</i>\n"
                f"• <i>'Oylik 1 million tushdi'</i>",
                parse_mode="HTML"
            )
            return

        # Amaliyot turini aniqlash
        tr_type = preselected_type if preselected_type in ("income", "expense") else data.get("type", "expense")
        amount = float(data.get("amount", 0))
        category = data.get("category") or ("📦 Boshqa kirim" if tr_type == "income" else "📦 Boshqa chiqim")
        comment = data.get("comment", "")
        transcript = data.get("transcript", "")

        # Vaqtinchalik xotiraga saqlash
        pending_id = pm.create_pending(
            user_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username,
            tr_type=tr_type,
            amount=amount,
            category=category,
            comment=comment,
            transcript=transcript
        )

        pending_data = pm.get_pending(pending_id)
        summary_text = pm.format_summary(pending_data, is_fix_mode=False)

        try:
            await processing_msg.delete()
        except Exception:
            pass

        # Done va Fix tugmalari bilan natijani ko'rsatish
        await message.answer(
            summary_text,
            reply_markup=get_confirm_keyboard(pending_id),
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Voice handler exception: {e}", exc_info=True)
        await processing_msg.edit_text(
            f"⚠️ Ovozli xabarni qabul qilishda xatolik yuz berdi:\n<code>{str(e)[:200]}</code>",
            parse_mode="HTML"
        )


# =========================================================================
# TASDIQLASH (DONE), TO'G'RILASH (FIX) VA O'ZGARTIRISH CALLBACKLARI
# =========================================================================

@router.callback_query(F.data.startswith("pdone_"))
async def process_done_callback(callback: CallbackQuery, state: FSMContext):
    """Done tugmasi bosilganda: ma'lumotni bazaga saqlash"""
    pending_id = callback.data.replace("pdone_", "")
    data = pm.pop_pending(pending_id)
    await state.clear()

    if not data:
        await callback.answer("⏳ Bu amal eskirgan yoki saqlab bo'lingan.", show_alert=True)
        try:
            await callback.message.delete()
        except Exception:
            pass
        return

    saved = await pm.save_pending_to_db(data)
    balance_info = saved["balance_info"]

    tr_type = data["type"]
    sign = "🟢 +" if tr_type == "income" else "🔴 -"
    type_label = "Kirim" if tr_type == "income" else "Chiqim"

    response = (
        f"✅ <b>{type_label} muvaffaqiyatli saqlandi!</b>\n\n"
        f"💵 <b>Summa:</b> {sign}{format_money(data['amount'])}\n"
        f"🏷 <b>Toifa:</b> {data['category']}\n"
    )
    if data.get("comment"):
        response += f"📝 <b>Izoh:</b> {data['comment']}\n"
    response += f"\n💰 <b>Joriy sof balans:</b> {format_money(balance_info['balance'])}"

    await callback.message.edit_text(response, parse_mode="HTML")
    await callback.answer("✅ Muvaffaqiyatli saqlandi!")


@router.callback_query(F.data.startswith("pfix_"))
async def process_fix_callback(callback: CallbackQuery, state: FSMContext):
    """Fix tugmasi bosilganda: o'zgartirish menyusini ko'rsatish"""
    pending_id = callback.data.replace("pfix_", "")
    data = pm.get_pending(pending_id)

    if not data:
        await callback.answer("⏳ Bu amal eskirgan.", show_alert=True)
        try:
            await callback.message.delete()
        except Exception:
            pass
        return

    summary = pm.format_summary(data, is_fix_mode=True)
    await callback.message.edit_text(
        summary,
        reply_markup=get_fix_keyboard(pending_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pcancel_"))
async def process_cancel_callback(callback: CallbackQuery, state: FSMContext):
    """Bekor qilish"""
    pending_id = callback.data.replace("pcancel_", "")
    pm.delete_pending(pending_id)
    await state.clear()

    await callback.message.edit_text("❌ <b>Amal bekor qilindi.</b>", parse_mode="HTML")
    await callback.answer()


# ----- 1. Summani o'zgartirish -----
@router.callback_query(F.data.startswith("pedit_amt_"))
async def process_edit_amount_click(callback: CallbackQuery, state: FSMContext):
    pending_id = callback.data.replace("pedit_amt_", "")
    data = pm.get_pending(pending_id)
    if not data:
        await callback.answer("⏳ Amal eskirgan.", show_alert=True)
        return

    await state.set_state(PendingEditState.edit_amount)
    await state.update_data(pending_id=pending_id)

    await callback.message.edit_text(
        f"💵 Hozirgi summa: <b>{format_money(data['amount'])}</b>\n\n"
        f"Yangi summani kiriting (masalan: <code>50000</code> yoki <code>50k</code>):",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(PendingEditState.edit_amount, F.text)
async def process_new_amount_input(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_keyboard())
        return

    state_data = await state.get_data()
    pending_id = state_data.get("pending_id")
    data = pm.get_pending(pending_id)

    if not data:
        await state.clear()
        await message.answer("⏳ Amal eskirgan, qayta yuboring.", reply_markup=get_main_keyboard())
        return

    new_amount = parse_amount(message.text)
    if not new_amount or new_amount <= 0:
        await message.answer(
            "⚠️ Summani to'g'ri formatda kiriting (musbat son bo'lishi kerak).\n"
            "Masalan: <code>50000</code> yoki <code>50k</code>",
            parse_mode="HTML"
        )
        return

    data["amount"] = new_amount
    await state.clear()

    summary = pm.format_summary(data, is_fix_mode=True)
    await message.answer(
        f"✅ Summa yangilandi: <b>{format_money(new_amount)}</b>\n\n{summary}",
        reply_markup=get_fix_keyboard(pending_id),
        parse_mode="HTML"
    )


# ----- 2. Kirim/Chiqim turini o'zgartirish -----
@router.callback_query(F.data.startswith("pedit_type_"))
async def process_edit_type_click(callback: CallbackQuery, state: FSMContext):
    pending_id = callback.data.replace("pedit_type_", "")
    data = pm.get_pending(pending_id)
    if not data:
        await callback.answer("⏳ Amal eskirgan.", show_alert=True)
        return

    current = "Kirim" if data["type"] == "income" else "Chiqim"
    await callback.message.edit_text(
        f"🔄 Hozirgi tur: <b>{current}</b>\n\n"
        f"Kerakli turni tanlang:",
        reply_markup=get_type_keyboard(pending_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ptype_inc_") | F.data.startswith("ptype_exp_"))
async def process_type_selected(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith("ptype_inc_"):
        pending_id = callback.data.replace("ptype_inc_", "")
        new_type = "income"
    else:
        pending_id = callback.data.replace("ptype_exp_", "")
        new_type = "expense"

    data = pm.get_pending(pending_id)
    if not data:
        await callback.answer("⏳ Amal eskirgan.", show_alert=True)
        return

    data["type"] = new_type
    # Mos toifaga almashtirish
    if new_type == "income" and "chiqim" in data["category"].lower():
        data["category"] = "📦 Boshqa kirim"
    elif new_type == "expense" and "kirim" in data["category"].lower():
        data["category"] = "📦 Boshqa chiqim"

    type_label = "Kirim" if new_type == "income" else "Chiqim"
    summary = pm.format_summary(data, is_fix_mode=True)

    await callback.message.edit_text(
        f"✅ Tur yangilandi: <b>{type_label}</b>\n\n{summary}",
        reply_markup=get_fix_keyboard(pending_id),
        parse_mode="HTML"
    )
    await callback.answer()


# ----- 3. Izoh/Maqsadni o'zgartirish -----
@router.callback_query(F.data.startswith("pedit_comm_"))
async def process_edit_comment_click(callback: CallbackQuery, state: FSMContext):
    pending_id = callback.data.replace("pedit_comm_", "")
    data = pm.get_pending(pending_id)
    if not data:
        await callback.answer("⏳ Amal eskirgan.", show_alert=True)
        return

    await state.set_state(PendingEditState.edit_comment)
    await state.update_data(pending_id=pending_id)

    current = data.get("comment", "—")
    await callback.message.edit_text(
        f"📝 Hozirgi izoh: <b>{current or '—'}</b>\n\n"
        f"Yangi izoh yoki sarflash maqsadini yozing:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(PendingEditState.edit_comment, F.text)
async def process_new_comment_input(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_keyboard())
        return

    state_data = await state.get_data()
    pending_id = state_data.get("pending_id")
    data = pm.get_pending(pending_id)

    if not data:
        await state.clear()
        await message.answer("⏳ Amal eskirgan, qayta yuboring.", reply_markup=get_main_keyboard())
        return

    new_comment = message.text.strip()
    if len(new_comment) > 60:
        new_comment = new_comment[:57] + "..."

    data["comment"] = new_comment

    # Izohdan toifani qayta aniqlash
    parsed = parse_financial_intent(new_comment, forced_type=data["type"])
    if parsed.get("category"):
        data["category"] = parsed["category"]

    await state.clear()

    summary = pm.format_summary(data, is_fix_mode=True)
    await message.answer(
        f"✅ Izoh yangilandi: <b>{new_comment}</b>\n\n{summary}",
        reply_markup=get_fix_keyboard(pending_id),
        parse_mode="HTML"
    )
