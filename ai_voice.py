import json
import logging
from typing import Optional, Dict, Any
from google import genai
from google.genai import types
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

VOICE_SYSTEM_PROMPT = """
Sen shaxsiy moliya hisobchi botining yordamchisisan.
Foydalanuvchi o'zbek tilida (yoki rus/aralash) ovozli xabar yuboradi.
Ovozli xabarni diqqat bilan tinglab, undagi kirim yoki chiqim haqidagi ma'lumotlarni aniqla.

Quyidagi JSON formatda javob qaytar:
{
  "is_finance": true,
  "type": "expense" yoki "income",
  "amount": 50000,
  "category": "🍽 Oziq-ovqat",
  "comment": "qisqa izoh",
  "transcript": "eshitilgan gap matni"
}

Qoidalar:
1. "type": agar pul sarflangan bo'lsa "expense" (chiqim), pul tushgan/topilgan bo'lsa "income" (kirim).
2. "amount": faqat raqam (float yoki int). Masalan "yigirma besh ming" -> 25000, "1.5 million" -> 1500000, "ellik ming" -> 50000.
3. "category": 
   Chiqimlar uchun quyidagilardan eng mosini tanla:
   - "🍽 Oziq-ovqat"
   - "🚕 Transport & Yo'l"
   - "🏠 Uy & Kommunal"
   - "🛍 Kiyim & Xarid"
   - "☕️ Kafe & Restoran"
   - "💊 Salomatlik & Dori"
   - "📱 Aloqa & Internet"
   - "🎮 Ko'ngilochar"
   - "🎁 Ehson / Sovg'a"
   - "📦 Boshqa chiqim"
   
   Kirimlar uchun quyidagilardan eng mosini tanla:
   - "💼 Oylik maosh"
   - "💻 Frilans / Biznes"
   - "🎁 Sovg'a / Yordam"
   - "🔄 Qarz qaytishi"
   - "📈 Savdo / Foyda"
   - "📦 Boshqa kirim"
4. "comment": Qisqa izoh (masalan: "Tushlik", "Yandex taxi", "Bozorlik").
5. "transcript": Foydalanuvchi aytgan gapning aniq matni (o'zbek tilida).
6. Agar audio xabarda moliyaviy xarajat yoki daromad aytilmagan bo'lsa:
   {"is_finance": false, "transcript": "eshitilgan gap", "error": "Moliyaviy ma'lumot topilmadi"}

Faqat toza JSON qaytar!
"""


async def process_voice_audio(audio_bytes: bytes) -> Dict[str, Any]:
    """Telegram ovozli xabarini AI orqali tahlil qilish va moliyaviy ma'lumotlarni ajratish"""
    if not GEMINI_API_KEY:
        return {
            "success": False,
            "error_type": "no_api_key",
            "message": "GEMINI_API_KEY sozlanmagan"
        }

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type="audio/ogg"
                ),
                VOICE_SYSTEM_PROMPT
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )

        result_text = response.text.strip()
        data = json.loads(result_text)
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        logger.error(f"Ovozni qayta ishlashda xatolik: {e}")
        return {
            "success": False,
            "error_type": "api_error",
            "message": str(e)
        }
