import os
import re
import json
import logging
import tempfile
import subprocess
from typing import Dict, Any, Optional

import imageio_ffmpeg
import speech_recognition as sr
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# O'zbek va rus tillaridagi son so'zlari lug'ati
UZ_NUMBERS = {
    'nol': 0, 'bir': 1, 'ikki': 2, 'uch': 3, "to'rt": 4, "to‘rt": 4, 'tort': 4,
    'besh': 5, 'olti': 6, 'yetti': 7, 'sakkiz': 8, "to'qqiz": 9, "to‘qqiz": 9, 'toqqiz': 9,
    "o'n": 10, "o‘n": 10, 'on': 10, 'yigirma': 20, "o'ttiz": 30, "o‘ttiz": 30, 'ottiz': 30,
    'qirq': 40, 'ellik': 50, 'oltmish': 60, 'yetmish': 70, 'sakson': 80, "to'qson": 90, 'toqson': 90,
    'yuz': 100, 'ming': 1000, 'million': 1000000, 'yarim': 0.5,
    # Ruscha sonlar (aralash so'zlashuv holatlari uchun)
    'один': 1, 'два': 2, 'три': 3, 'четыре': 4, 'пять': 5, 'шесть': 6, 'семь': 7, 'восемь': 8, 'девять': 9,
    'десять': 10, 'двадцать': 20, 'тридцать': 30, 'сорок': 40, 'пятьдесят': 50, 'шестьдесят': 60,
    'семьдесят': 70, 'восемьдесят': 80, 'девяносто': 90, 'сто': 100, 'тысяч': 1000, 'тысяча': 1000, 'миллион': 1000000
}


def convert_ogg_to_wav(ogg_bytes: bytes) -> bytes:
    """Telegramning OGG formatidagi ovozini WAV formatiga o'tkazish"""
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as ogg_file:
        ogg_file.write(ogg_bytes)
        ogg_path = ogg_file.name

    wav_path = ogg_path + ".wav"
    try:
        cmd = [ffmpeg_exe, "-y", "-i", ogg_path, "-ar", "16000", "-ac", "1", wav_path]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        with open(wav_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(ogg_path):
            os.remove(ogg_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)


def transcribe_audio_free(wav_bytes: bytes) -> Optional[str]:
    """Bepul Google Speech Recognition orqali audio faylni matnga aylantirish"""
    recognizer = sr.Recognizer()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
        wav_file.write(wav_bytes)
        wav_path = wav_file.name

    try:
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            # Avval o'zbek tilida sinab ko'ramiz
            try:
                text = recognizer.recognize_google(audio_data, language="uz-UZ")
                return text
            except sr.UnknownValueError:
                # Agar o'zbekchada tushunmasa rus tilida sinaymiz
                return recognizer.recognize_google(audio_data, language="ru-RU")
    except Exception as e:
        logger.error(f"Free speech recognition error: {e}")
        return None
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)


def extract_number_from_text(text: str) -> Optional[float]:
    """Matndan summani aniqlash (raqamlar yoki so'zlar orqali)"""
    # 1. 35 000 kabi probelli sonlarni birlashtirish
    cleaned = re.sub(r'(\d+)\s+(\d{3})', r'\1\2', text)

    # 2. 50000, 50k, 1.5mln, 20 ming kabilarni tekshirish
    match = re.search(r'(\d+(?:[.,]\d+)?)\s*(k|ming|mln|million|m)?\b', cleaned.lower())
    if match:
        num_str = match.group(1).replace(',', '.')
        unit = match.group(2)
        try:
            val = float(num_str)
            if unit in ('k', 'ming'):
                val *= 1000
            elif unit in ('mln', 'million', 'm'):
                val *= 1000000
            if val > 0:
                return val
        except ValueError:
            pass

    # 3. So'z bilan aytilgan sonlarni raqamga aylantirish (masalan: "yigirma besh ming")
    tokens = text.lower().replace('-', ' ').split()
    total = 0
    current = 0
    found = False
    for t in tokens:
        clean_t = re.sub(r"[^\w']", '', t)
        if clean_t.isdigit():
            found = True
            current += float(clean_t)
        elif clean_t in UZ_NUMBERS:
            found = True
            val = UZ_NUMBERS[clean_t]
            if val == 1000000:
                if current == 0:
                    current = 1
                total += current * 1000000
                current = 0
            elif val == 1000:
                if current == 0:
                    current = 1
                total += current * 1000
                current = 0
            elif val == 100:
                if current == 0:
                    current = 1
                current = current * 100
            elif val == 0.5:
                current += 0.5
            else:
                current += val
    total += current
    return total if found and total > 0 else None


def parse_financial_intent(transcript: str) -> Dict[str, Any]:
    """Ovozdan olingan matndan moliyaviy ma'lumotlarni ajratib olish"""
    amount = extract_number_from_text(transcript)
    if not amount or amount <= 0:
        return {
            "is_finance": False,
            "transcript": transcript,
            "error": "Summa aniqlanmadi"
        }

    low = transcript.lower()

    # Kirimga tegishli kalit so'zlar
    income_words = [
        "oylik", "maosh", "avans", "ish haqi", "daromad", "tushdi", "tushgan",
        "topdim", "berishdi", "keldi", "qarz qaytdi", "qarzini berdi",
        "savdo", "foyda", "mukofot", "premiya", "zarplata"
    ]
    is_income = any(w in low for w in income_words)
    tr_type = "income" if is_income else "expense"

    # Toifalarni aniqlash
    category = "📦 Boshqa chiqim" if tr_type == "expense" else "📦 Boshqa kirim"
    if tr_type == "expense":
        if any(w in low for w in ["ovqat", "bozor", "non", "go'sht", "gosht", "suv", "tushlik", "osh", "somsa", "lavash", "market", "korzinka", "makro"]):
            category = "🍽 Oziq-ovqat"
        elif any(w in low for w in ["taxi", "taksi", "benzin", "yo'l", "yol", "yo'lkira", "zapravka", "propan", "metan", "avtobus", "metro"]):
            category = "🚕 Transport & Yo'l"
        elif any(w in low for w in ["kafe", "restoran", "kofe", "coffee", "choyxona", "oshxona", "lunch"]):
            category = "☕️ Kafe & Restoran"
        elif any(w in low for w in ["svet", "gaz", "suv", "kommunal", "ijara", "kvartira", "dom", "remont"]):
            category = "🏠 Uy & Kommunal"
        elif any(w in low for w in ["kiyim", "shim", "ko'ylak", "koylak", "oyoq kiyim", "tufli", "krossovka", "shop"]):
            category = "🛍 Kiyim & Xarid"
        elif any(w in low for w in ["dori", "apteka", "doktor", "shifoxona", "klinika", "tish"]):
            category = "💊 Salomatlik & Dori"
        elif any(w in low for w in ["internet", "paynet", "telefon", "megabayt", "tarif", "wifi"]):
            category = "📱 Aloqa & Internet"
        elif any(w in low for w in ["kino", "o'yin", "oyin", "dam", "sayohat"]):
            category = "🎮 Ko'ngilochar"
        elif any(w in low for w in ["ehson", "sadaqa", "masjid", "sovg'a", "sovga", "hadya"]):
            category = "🎁 Ehson / Sovg'a"
    else:
        if any(w in low for w in ["oylik", "maosh", "avans", "ish haqi", "zarplata"]):
            category = "💼 Oylik maosh"
        elif any(w in low for w in ["frilans", "loyiha", "mijoz", "dastur", "zakaz", "dizayn"]):
            category = "💻 Frilans / Biznes"
        elif any(w in low for w in ["qarz", "qaytgan"]):
            category = "🔄 Qarz qaytishi"
        elif any(w in low for w in ["sovga", "sovg'a", "mukofot", "yordam"]):
            category = "🎁 Sovg'a / Yordam"
        elif any(w in low for w in ["foyda", "savdo"]):
            category = "📈 Savdo / Foyda"

    comment = transcript.strip()
    if len(comment) > 60:
        comment = comment[:57] + "..."

    return {
        "is_finance": True,
        "type": tr_type,
        "amount": amount,
        "category": category,
        "comment": comment,
        "transcript": transcript
    }


async def process_voice_audio(audio_bytes: bytes) -> Dict[str, Any]:
    """
    Ovozli xabarni tahlil qilish:
    1. Agar GEMINI_API_KEY bo'lsa, Gemini AI orqali.
    2. Agar bo'lmasa, mutlaqo bepul Google Speech Recognition + ichki tahlilchi orqali!
    """
    # 1. Agar Gemini AI kaliti berilgan bo'lsa
    if GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type="audio/ogg"
                    ),
                    "Ushbu audio xabarda aytilgan moliyaviy ma'lumotni (kirim yoki chiqim) aniqlab, faqat quyidagi JSON formatida qaytar:\n"
                    "{\n"
                    '  "is_finance": true,\n'
                    '  "type": "expense" yoki "income",\n'
                    '  "amount": 50000,\n'
                    '  "category": "🍽 Oziq-ovqat",\n'
                    '  "comment": "qisqa izoh",\n'
                    '  "transcript": "eshitilgan gap matni"\n'
                    "}\n"
                    "Agar moliyaviy ma'lumot topilmasa: {\"is_finance\": false, \"transcript\": \"...\"}"
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            data = json.loads(response.text.strip())
            return {"success": True, "data": data}
        except Exception as e:
            logger.warning(f"Gemini API xatoligi, bepul vositaga o'tilmoqda: {e}")

    # 2. Bepul Speech Recognition + O'zbekcha parser (API kalitsiz ishlaydi!)
    try:
        wav_bytes = convert_ogg_to_wav(audio_bytes)
        transcript = transcribe_audio_free(wav_bytes)

        if not transcript:
            return {
                "success": False,
                "error_type": "no_speech",
                "message": "Ovoz aniq eshitilmadi yoki gapirilmadi."
            }

        parsed = parse_financial_intent(transcript)
        return {
            "success": True,
            "data": parsed
        }
    except Exception as e:
        logger.error(f"Ovozni bepul tahlil qilishda xatolik: {e}")
        return {
            "success": False,
            "error_type": "processing_error",
            "message": str(e)
        }
