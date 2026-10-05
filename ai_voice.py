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
from locales import CAT_UZ_TO_RU, CAT_RU_TO_UZ

logger = logging.getLogger(__name__)

# O'zbek va rus tillaridagi barcha son so'zlari lug'ati
NUMBERS_DICT = {
    # O'zbekcha
    'nol': 0, 'bir': 1, 'ikki': 2, 'uch': 3, "to'rt": 4, "to‘rt": 4, 'tort': 4,
    'besh': 5, 'olti': 6, 'yetti': 7, 'sakkiz': 8, "to'qqiz": 9, "to‘qqiz": 9, 'toqqiz': 9,
    "o'n": 10, "o‘n": 10, 'on': 10, 'yigirma': 20, "o'ttiz": 30, "o‘ttiz": 30, 'ottiz': 30,
    'qirq': 40, 'ellik': 50, 'oltmish': 60, 'yetmish': 70, 'sakson': 80, "to'qson": 90, 'toqson': 90,
    'yuz': 100, 'ming': 1000, 'million': 1000000, 'yarim': 0.5,

    # Ruscha
    'ноль': 0, 'один': 1, 'одна': 1, 'два': 2, 'две': 2, 'три': 3, 'четыре': 4, 'пять': 5,
    'шесть': 6, 'семь': 7, 'восемь': 8, 'девять': 9, 'десять': 10,
    'одиннадцать': 11, 'двенадцать': 12, 'тринадцать': 13, 'четырнадцать': 14, 'пятнадцать': 15,
    'шестнадцать': 16, 'семнадцать': 17, 'восемнадцать': 18, 'девятнадцать': 19,
    'двадцать': 20, 'тридцать': 30, 'сорок': 40, 'пятьдесят': 50, 'шестьдесят': 60,
    'семьдесят': 70, 'восемьдесят': 80, 'девяносто': 90,
    'сто': 100, 'двести': 200, 'триста': 300, 'четыреста': 400, 'пятьсот': 500,
    'шестьсот': 600, 'семьсот': 700, 'восемьсот': 800, 'девятьсот': 900,
    'тысяча': 1000, 'тысячи': 1000, 'тысяч': 1000, 'тыс': 1000,
    'миллион': 1000000, 'миллиона': 1000000, 'миллионов': 1000000,
    'полтора': 1.5, 'половина': 0.5, 'полмиллиона': 500000
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
            try:
                os.remove(ogg_path)
            except OSError:
                pass
        if os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except OSError:
                pass


def transcribe_audio_free(wav_bytes: bytes, user_lang: str = "uz") -> Optional[str]:
    """
    Bepul Google Speech Recognition orqali ko'p tilli (o'zbek va rus) nutqni matnga aylantirish.
    Foydalanuvchi qaysi tilni tanlaganidan qat'i nazar (rus yoki o'zbek), har ikkala tilda
    nutq tekshiriladi va eng aniq moliyaviy ma'lumot (summa + toifa) topilgan variant tanlanadi.
    """
    recognizer = sr.Recognizer()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
        wav_file.write(wav_bytes)
        wav_path = wav_file.name

    try:
        with sr.AudioFile(wav_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio_data = recognizer.record(source)

            # Foydalanuvchi tanlagan til bo'yicha ketma-ketlik
            primary_lang = "ru-RU" if user_lang == "ru" else "uz-UZ"
            secondary_lang = "uz-UZ" if user_lang == "ru" else "ru-RU"

            candidates = []

            for l_code in [primary_lang, secondary_lang]:
                try:
                    text = recognizer.recognize_google(audio_data, language=l_code)
                    if text and text.strip():
                        p = parse_financial_intent(text)
                        score = 0
                        if p.get("is_finance"):
                            score += 10
                        if p.get("amount") and p["amount"] > 0:
                            score += 10
                        if p.get("category") and "boshqa" not in p["category"].lower() and "другие" not in p["category"].lower():
                            score += 5
                        candidates.append((score, text))
                        # Agar birinchi tildayoq to'liq ma'lumot (summa + toifa) topilsa
                        if score >= 25:
                            return text
                except (sr.UnknownValueError, sr.RequestError):
                    continue

            if not candidates:
                # Ingliz / aralash sinash
                try:
                    text = recognizer.recognize_google(audio_data, language="en-US")
                    if text and text.strip():
                        return text
                except (sr.UnknownValueError, sr.RequestError):
                    pass
                return None

            # Eng yuqori moliyaviy ball to'plagan variantni tanlash
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]
    except Exception as e:
        logger.error(f"Free speech recognition error: {e}")
        return None
    finally:
        if os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except OSError:
                pass


def extract_number_from_text(text: str) -> Optional[float]:
    """O'zbek va rus tillaridagi matndan summani aniqlash (raqamlar yoki so'zlar)"""
    if not text:
        return None

    # 1. 35 000 yoki 150 000 kabi probelli sonlarni birlashtirish
    cleaned = re.sub(r'(\d+)\s+(\d{3})', r'\1\2', text)

    # 2. Avval son va birlik (k, ming, mln, million, тыс, млн...) ni qidirish
    match = re.search(r'(\d+(?:[.,]\d+)?)\s*(k|ming|mln|million|m|тыс|тысяч|тысячи|тысяча|млн|миллион|миллиона|миллионов|к)\b', cleaned.lower())
    if match:
        num_str = match.group(1).replace(',', '.')
        unit = match.group(2)
        try:
            val = float(num_str)
            if unit in ('k', 'ming', 'тыс', 'тысяч', 'тысячи', 'тысяча', 'к'):
                val *= 1000
            elif unit in ('mln', 'million', 'm', 'млн', 'миллион', 'миллиона', 'миллионов'):
                val *= 1000000
            if val > 0:
                return val
        except ValueError:
            pass

    # 3. Agar birliksiz oddiy son bo'lsa
    match = re.search(r'\b(\d+(?:[.,]\d+)?)\b', cleaned)
    if match:
        try:
            val = float(match.group(1).replace(',', '.'))
            if val > 0:
                return val
        except ValueError:
            pass

    # 3. So'z bilan aytilgan sonlarni raqamga aylantirish (uz & ru)
    tokens = text.lower().replace('-', ' ').split()
    total = 0
    current = 0
    found = False
    for t in tokens:
        clean_t = re.sub(r"[^\w']", '', t)
        if clean_t.isdigit():
            found = True
            current += float(clean_t)
        elif clean_t in NUMBERS_DICT:
            found = True
            val = NUMBERS_DICT[clean_t]
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
            elif val >= 100:
                if val == 100 and current in (1, 2, 3, 4, 5, 6, 7, 8, 9):
                    current = current * 100
                else:
                    current += val
            elif val == 1.5:
                current = (current if current > 0 else 1) * 1.5
            elif val == 0.5:
                current += 0.5
            elif val == 500000:
                total += 500000
            else:
                current += val
    total += current
    return total if found and total > 0 else None


def parse_financial_intent(transcript: str, forced_type: Optional[str] = None) -> Dict[str, Any]:
    """
    O'zbek, rus yoki aralash tildagi matn/ovozdan moliyaviy ma'lumotlarni ajratib olish
    """
    amount = extract_number_from_text(transcript)
    if not amount or amount <= 0:
        return {
            "is_finance": False,
            "transcript": transcript,
            "error": "Summa aniqlanmadi"
        }

    low = transcript.lower()

    # Kirim kalit so'zlari (o'zbekcha + ruscha)
    income_words = [
        # O'zbekcha
        "oylik", "maosh", "avans", "ish haqi", "daromad", "tushdi", "tushgan",
        "topdim", "berishdi", "keldi", "qarz qaytdi", "qarzini berdi",
        "savdo", "foyda", "mukofot", "premiya",
        # Ruscha
        "зарплата", "зарплату", "зарплаты", "зарплате", "зп", "получка", "аванс",
        "доход", "доходы", "прибыль", "пришло", "приход", "получил", "получила",
        "получили", "перевели", "перечислили", "вернули долг", "отдали долг",
        "заработал", "заработала", "выручка", "премия"
    ]

    if forced_type in ("income", "expense"):
        tr_type = forced_type
    else:
        is_income = any(w in low for w in income_words)
        tr_type = "income" if is_income else "expense"

    # Toifalarni aniqlash (o'zbekcha va ruscha kalit so'zlar)
    category = "📦 Boshqa chiqim" if tr_type == "expense" else "📦 Boshqa kirim"
    if tr_type == "expense":
        if any(w in low for w in [
            "ovqat", "bozor", "non", "go'sht", "gosht", "suv", "tushlik", "osh", "somsa", "lavash",
            "market", "korzinka", "makro", "еда", "продукты", "обед", "ужин", "завтрак", "покушать",
            "перекус", "мясо", "хлеб", "супермаркет", "магазин", "базар", "шаурма", "пицца", "донер"
        ]):
            category = "🍽 Oziq-ovqat"
        elif any(w in low for w in [
            "taxi", "taksi", "benzin", "yo'l", "yol", "yo'lkira", "zapravka", "propan", "metan",
            "avtobus", "metro", "такси", "бензин", "проезд", "заправка", "газ", "метро", "автобус",
            "маршрутка", "дорога"
        ]):
            category = "🚕 Transport & Yo'l"
        elif any(w in low for w in [
            "kafe", "restoran", "kofe", "coffee", "choyxona", "oshxona", "lunch",
            "кафе", "ресторан", "кофе", "кофейня", "чайхана", "столовая", "бар"
        ]):
            category = "☕️ Kafe & Restoran"
        elif any(w in low for w in [
            "svet", "gaz", "suv", "kommunal", "ijara", "kvartira", "dom", "remont",
            "свет", "газ", "вода", "коммуналка", "аренда", "квартира", "дом", "ремонт", "жкх"
        ]):
            category = "🏠 Uy & Kommunal"
        elif any(w in low for w in [
            "kiyim", "shim", "ko'ylak", "koylak", "oyoq kiyim", "tufli", "krossovka", "shop",
            "одежда", "обувь", "куртка", "штаны", "кроссовки", "покупки", "шоппинг"
        ]):
            category = "🛍 Kiyim & Xarid"
        elif any(w in low for w in [
            "dori", "apteka", "doktor", "shifoxona", "klinika", "tish",
            "аптека", "лекарства", "таблетки", "врач", "больница", "клиника", "стоматолог", "зубы"
        ]):
            category = "💊 Salomatlik & Dori"
        elif any(w in low for w in [
            "internet", "paynet", "telefon", "megabayt", "tarif", "wifi",
            "интернет", "связь", "телефон", "тариф", "мегабайты", "баланс"
        ]):
            category = "📱 Aloqa & Internet"
        elif any(w in low for w in [
            "kino", "o'yin", "oyin", "dam", "sayohat",
            "кино", "фильм", "игры", "отдых", "кинотеатр", "билеты", "путешествие"
        ]):
            category = "🎮 Ko'ngilochar"
        elif any(w in low for w in [
            "ehson", "sadaqa", "masjid", "sovg'a", "sovga", "hadya",
            "подарок", "подарки", "благотворительность", "донат", "помощь", "мечеть"
        ]):
            category = "🎁 Ehson / Sovg'a"
    else:
        if any(w in low for w in [
            "oylik", "maosh", "avans", "ish haqi", "zarplata",
            "зарплата", "зарплату", "зарплаты", "зп", "получка", "аванс", "оклад"
        ]):
            category = "💼 Oylik maosh"
        elif any(w in low for w in [
            "frilans", "loyiha", "mijoz", "dastur", "zakaz", "dizayn",
            "фриланс", "проект", "клиент", "заказ", "разработка", "дизайн"
        ]):
            category = "💻 Frilans / Biznes"
        elif any(w in low for w in ["qarz", "qaytgan", "долг", "вернули", "отдали"]):
            category = "🔄 Qarz qaytishi"
        elif any(w in low for w in ["sovga", "sovg'a", "mukofot", "yordam", "подарок", "помощь", "перевели", "подарили"]):
            category = "🎁 Sovg'a / Yordam"
        elif any(w in low for w in ["foyda", "savdo", "выручка", "прибыль", "продажи", "торговля"]):
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


async def process_voice_audio(audio_bytes: bytes, forced_type: Optional[str] = None, user_lang: str = "uz") -> Dict[str, Any]:
    """
    Ovozli xabarni ko'p tilli (o'zbek va rus) tahlil qilish
    """
    # 1. Agar Gemini AI kaliti berilgan bo'lsa
    if GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=GEMINI_API_KEY)
            type_hint = f" Amaliyot turi (Kirim yoki Chiqim): {forced_type}." if forced_type else ""
            response = await client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type="audio/ogg"
                    ),
                    f"Foydalanuvchi o'zbek tilida, rus tilida yoki aralash (ruscha-o'zbekcha) gapirishi mumkin. "
                    f"Ushbu audio xabarda aytilgan moliyaviy ma'lumotni (kirim yoki chiqim / доход или расход) aniqlab, faqat quyidagi JSON formatida qaytar.{type_hint}\n"
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
            if forced_type in ("income", "expense"):
                data["type"] = forced_type
            return {"success": True, "data": data}
        except Exception as e:
            logger.warning(f"Gemini API xatoligi, bepul ko'p tilli vositaga o'tilmoqda: {e}")

    # 2. Bepul nutqni aniqlash + o'zbek/rus tahlilchi
    try:
        logger.info(f"Ovoz qabul qilindi ({len(audio_bytes)} bayt). WAV ga aylantirilmoqda...")
        wav_bytes = convert_ogg_to_wav(audio_bytes)
        logger.info(f"WAV ga aylantirildi ({len(wav_bytes)} bayt). Ko'p tilli nutq aniqlanmoqda (user_lang={user_lang})...")
        transcript = transcribe_audio_free(wav_bytes, user_lang=user_lang)

        if not transcript:
            logger.warning("Ovozdan hech qanday so'z tanib olinmadi.")
            return {
                "success": False,
                "error_type": "no_speech",
                "message": "Ovoz aniq eshitilmadi yoki gapirilmadi."
            }

        logger.info(f"Eshitilgan matn: '{transcript}'. Moliyaviy tahlil qilinmoqda...")
        parsed = parse_financial_intent(transcript, forced_type=forced_type)
        logger.info(f"Tahlil natijasi: {parsed}")
        return {
            "success": True,
            "data": parsed
        }
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
        logger.error(f"FFmpeg xatoligi: {err_msg}")
        return {
            "success": False,
            "error_type": "processing_error",
            "message": f"Audio xatolik: {err_msg}"
        }
    except Exception as e:
        logger.error(f"Ovozni tahlil qilishda xatolik: {e}", exc_info=True)
        return {
            "success": False,
            "error_type": "processing_error",
            "message": str(e)
        }
