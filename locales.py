# -*- coding: utf-8 -*-
"""
Bilingual localization module (Uzbek & Russian)
O'zbek va rus tillari uchun mahalliylashtirish moduli
"""

from typing import Dict, Any, List, Tuple


# Toifalar ro'yxati (uz & ru)
EXPENSE_CATEGORIES_UZ: List[Tuple[str, str]] = [
    ("🍽 Oziq-ovqat", "cat_exp_food"),
    ("🚕 Transport & Yo'l", "cat_exp_transport"),
    ("🏠 Uy & Kommunal", "cat_exp_home"),
    ("🛍 Kiyim & Xarid", "cat_exp_shopping"),
    ("☕️ Kafe & Restoran", "cat_exp_cafe"),
    ("💊 Salomatlik & Dori", "cat_exp_health"),
    ("📱 Aloqa & Internet", "cat_exp_internet"),
    ("🎮 Ko'ngilochar", "cat_exp_fun"),
    ("🎁 Ehson / Sovg'a", "cat_exp_gift"),
    ("📦 Boshqa chiqim", "cat_exp_other"),
]

EXPENSE_CATEGORIES_RU: List[Tuple[str, str]] = [
    ("🍽 Продукты & Еда", "cat_exp_food"),
    ("🚕 Транспорт & Такси", "cat_exp_transport"),
    ("🏠 Дом & Коммуналка", "cat_exp_home"),
    ("🛍 Одежда & Покупки", "cat_exp_shopping"),
    ("☕️ Кафе & Рестораны", "cat_exp_cafe"),
    ("💊 Здоровье & Аптека", "cat_exp_health"),
    ("📱 Связь & Интернет", "cat_exp_internet"),
    ("🎮 Развлечения", "cat_exp_fun"),
    ("🎁 Подарки & Помощь", "cat_exp_gift"),
    ("📦 Другие расходы", "cat_exp_other"),
]

INCOME_CATEGORIES_UZ: List[Tuple[str, str]] = [
    ("💼 Oylik maosh", "cat_inc_salary"),
    ("💻 Frilans / Biznes", "cat_inc_freelance"),
    ("🎁 Sovg'a / Yordam", "cat_inc_gift"),
    ("🔄 Qarz qaytishi", "cat_inc_debt"),
    ("📈 Savdo / Foyda", "cat_inc_trade"),
    ("📦 Boshqa kirim", "cat_inc_other"),
]

INCOME_CATEGORIES_RU: List[Tuple[str, str]] = [
    ("💼 Зарплата", "cat_inc_salary"),
    ("💻 Фриланс / Бизнес", "cat_inc_freelance"),
    ("🎁 Подарок / Помощь", "cat_inc_gift"),
    ("🔄 Возврат долга", "cat_inc_debt"),
    ("📈 Торговля / Прибыль", "cat_inc_trade"),
    ("📦 Другие доходы", "cat_inc_other"),
]

# Toifa ID si bo'yicha nomini olish
CATEGORY_MAP_UZ = dict(EXPENSE_CATEGORIES_UZ + INCOME_CATEGORIES_UZ)
CATEGORY_MAP_RU = dict(EXPENSE_CATEGORIES_RU + INCOME_CATEGORIES_RU)

# Matndan toifani tarjima qilish
CAT_UZ_TO_RU = {
    "🍽 Oziq-ovqat": "🍽 Продукты & Еда",
    "🚕 Transport & Yo'l": "🚕 Транспорт & Такси",
    "🏠 Uy & Kommunal": "🏠 Дом & Коммуналка",
    "🛍 Kiyim & Xarid": "🛍 Одежда & Покупки",
    "☕️ Kafe & Restoran": "☕️ Кафе & Рестораны",
    "💊 Salomatlik & Dori": "💊 Здоровье & Аптека",
    "📱 Aloqa & Internet": "📱 Связь & Интернет",
    "🎮 Ko'ngilochar": "🎮 Развлечения",
    "🎁 Ehson / Sovg'a": "🎁 Подарки & Помощь",
    "📦 Boshqa chiqim": "📦 Другие расходы",
    "💼 Oylik maosh": "💼 Зарплата",
    "💻 Frilans / Biznes": "💻 Фриланс / Бизнес",
    "🎁 Sovg'a / Yordam": "🎁 Подарок / Помощь",
    "🔄 Qarz qaytishi": "🔄 Возврат долга",
    "📈 Savdo / Foyda": "📈 Торговля / Прибыль",
    "📦 Boshqa kirim": "📦 Другие доходы",
}

CAT_RU_TO_UZ = {v: k for k, v in CAT_UZ_TO_RU.items()}


def localize_category(cat: str, lang: str) -> str:
    """Toifani foydalanuvchi tiliga moslashtirish"""
    if lang == "ru":
        return CAT_UZ_TO_RU.get(cat, cat)
    return CAT_RU_TO_UZ.get(cat, cat)


MESSAGES = {
    "uz": {
        "choose_lang": "🌐 <b>Iltimos, o'zingiz uchun qulay tilni tanlang:</b>\n"
                       "Пожалуйста, выберите удобный для вас язык:",
        "lang_selected": "✅ <b>O'zbek tili tanlandi!</b>\n"
                         "Marhamat, botdan foydalanishingiz mumkin 👇",
        "welcome": (
            "Assalomu alaykum, <b>{name}</b>! 💰\n\n"
            "Men sizning shaxsiy <b>Moliya hisobchi botingizman</b>.\n\n"
            "✨ <b>Imkoniyatlar:</b>\n"
            "• <b>💰 Kirim</b> va <b>💳 Chiqim</b> tugmalari orqali hisob-kitob qilish;\n"
            "• 🎙 <b>Ovozli xabar</b> yuborish (o'zbek yoki rus tilida) — AI uni eshitib tahlil qiladi;\n"
            "• <b>✅ Done</b> (Tasdiqlash) va <b>✏️ Fix</b> (To'g'rilash) tugmalari orqali tekshirib saqlash;\n"
            "• <b>📊 Statistika</b> va <b>💰 Balans</b>ni doimiy kuzatib borish!\n\n"
            "Pastdagi menyu orqali boshlashingiz mumkin 👇"
        ),
        "btn_income": "💰 Kirim",
        "btn_expense": "💳 Chiqim",
        "btn_stats": "📊 Statistika & Hisobot",
        "btn_balance": "💰 Mening balansim",
        "btn_history": "🕒 Oxirgi amallar",
        "btn_help": "ℹ️ Qanday ishlatiladi?",
        "btn_lang": "🌐 Til / Язык",
        "btn_cancel": "❌ Bekor qilish",
        "placeholder": "Kirim yoki Chiqimni tanlang, yozing yoki ovoz yuboring...",
        "income_prompt": (
            "🟢 <b>Kirim bo'limi tanlandi!</b>\n\n"
            "Summa va maqsadini <b>yozing</b> (masalan: <i>'500 000 oylik'</i> yoki <i>'100k frilans'</i>)\n"
            "yoki 🎙 <b>ovozli xabar</b> yuboring:"
        ),
        "expense_prompt": (
            "🔴 <b>Chiqim bo'limi tanlandi!</b>\n\n"
            "Summa va nima uchunligini <b>yozing</b> (masalan: <i>'25 000 tushlik'</i> yoki <i>'15k taxi'</i>)\n"
            "yoki 🎙 <b>ovozli xabar</b> yuboring:"
        ),
        "voice_processing": "🎙 <i>Ovozingiz eshitilmoqda va AI tomonidan tahlil qilinmoqda...</i>",
        "voice_no_speech": (
            "🎙 <b>Ovoz aniq eshitilmadi.</b>\n\n"
            "Iltimos, mikrofonga yaqinroq gapiring yoki yozma shaklda yuboring "
            "(masalan: <i>'25 000 tushlik'</i>)."
        ),
        "voice_no_amount": (
            "🎙 <b>Eshitildi:</b> «<i>{transcript}</i>»\n\n"
            "⚠️ Ovozdan summa aniqlanmadi.\n"
            "Iltimos, summani ham aytib o'ting (masalan: <i>'Tushlik 25 ming'</i>)."
        ),
        "voice_error": "⚠️ Ovozni tahlil qilishda xatolik yuz berdi:\n<code>{error}</code>",
        "heard": "Eshitildi",
        "summary_title": "Aniqlangan ma'lumot:",
        "type_label": "Tur",
        "income_name": "Kirim",
        "expense_name": "Chiqim",
        "amount_label": "Summa",
        "category_label": "Toifa",
        "comment_label": "Izoh/Maqsad",
        "is_correct_question": "Ma'lumotlar to'g'rimi?",
        "which_part_question": "Qaysi qismini o'zgartirmoqchisiz?",
        "btn_done": "✅ Done — Tasdiqlash",
        "btn_fix": "✏️ Fix — To'g'rilash",
        "btn_edit_amount": "💵 Summani o'zgartirish",
        "btn_edit_type": "🔄 Kirim/Chiqim o'zgartirish",
        "btn_edit_comment": "📝 Izoh/Maqsad o'zgartirish",
        "btn_ready_save": "✅ Tayyor — Saqlash",
        "saved_success": "muvaffaqiyatli saqlandi!",
        "current_balance": "Joriy sof balans:",
        "cancelled": "Amal bekor qilindi.",
        "expired": "⏳ Bu amal eskirgan yoki saqlab bo'lingan.",
        "edit_amount_prompt": "💵 Hozirgi summa: <b>{amount}</b>\n\nYangi summani kiriting (masalan: <code>50000</code> yoki <code>50k</code>):",
        "amount_updated": "Summa yangilandi:",
        "edit_type_prompt": "🔄 Hozirgi tur: <b>{type}</b>\n\nKerakli turni tanlang:",
        "type_updated": "Tur yangilandi:",
        "edit_comment_prompt": "📝 Hozirgi izoh: <b>{comment}</b>\n\nYangi izoh yoki sarflash maqsadini yozing:",
        "comment_updated": "Izoh yangilandi:",
        "balance_title": "💳 <b>Sizning umumiy moliyaviy balansingiz:</b>",
        "total_income": "Jami kirim",
        "total_expense": "Jami chiqim",
        "net_savings": "Sof jamg'arma",
        "report_prompt": "📊 <b>Qaysi davr bo'yicha hisobot ko'rmoqchisiz?</b>\n\nQuyidagi tugmalardan birini tanlang:",
        "report_today": "📅 Bugun",
        "report_yesterday": "📆 Kecha",
        "report_week": "🗓 Oxirgi 7 kun",
        "report_month": "📊 Shu oy",
        "report_last_month": "📈 O'tgan oy",
        "report_all": "💰 Umumiy balans",
        "no_history": "🕒 Sizda hali hech qanday amallar tarixi mavjud emas.",
        "recent_history_title": "🕒 <b>Oxirgi amallaringiz:</b>",
        "delete_action": "o'chirish",
        "deleted_success": "Amal o'chirildi.",
        "help_text": (
            "💡 <b>Botdan foydalanish bo'yicha qo'llanma</b>\n\n"
            "<b>1. Kirim yoki Chiqim kiritish:</b>\n"
            "• Pastdagi <b>💰 Kirim</b> yoki <b>💳 Chiqim</b> tugmasini bosing;\n"
            "• Summa va maqsadini yozing (masalan: <code>25 000 tushlik</code>) yoki 🎙 <b>ovozli xabar</b> yuboring;\n"
            "• <b>✅ Done</b> tugmasi bilan tasdiqlang yoki <b>✏️ Fix</b> bilan xatolikni to'g'rilang!\n\n"
            "<b>2. Ovozli xabar:</b>\n"
            "O'zbekcha yoki ruscha bemalol gapiring — AI summani va maqsadini avtomatik ajratadi!\n\n"
            "<b>3. Tezkor yozuv:</b>\n"
            "• <code>-15000 tushlik</code> yoki <code>-20k taxi</code>\n"
            "• <code>+500000 oylik</code> yoki <code>+100k frilans</code>\n\n"
            "<b>4. Tilni o'zgartirish:</b>\n"
            "• <b>🌐 Til / Язык</b> tugmasi orqali istalgan vaqtda tilni almashtiring."
        ),
    },
    "ru": {
        "choose_lang": "🌐 <b>Пожалуйста, выберите удобный для вас язык:</b>\n"
                       "Iltimos, o'zingiz uchun qulay tilni tanlang:",
        "lang_selected": "✅ <b>Выбран русский язык!</b>\n"
                         "Добро пожаловать, можете начинать пользоваться ботом 👇",
        "welcome": (
            "Здравствуйте, <b>{name}</b>! 💰\n\n"
            "Я ваш личный <b>Финансовый помощник и бот учёта доходов и расходов</b>.\n\n"
            "✨ <b>Возможности:</b>\n"
            "• Учёт расходов и доходов по кнопкам <b>💰 Доход</b> и <b>💳 Расход</b>;\n"
            "• 🎙 <b>Голосовые сообщения</b> (на русском или узбекском) — ИИ распознаёт сумму и цель;\n"
            "• Кнопки <b>✅ Done</b> (Подтвердить) и <b>✏️ Fix</b> (Исправить) для контроля точности;\n"
            "• <b>📊 Статистика</b> и <b>💰 Баланс</b> в один клик!\n\n"
            "Выберите нужное действие в меню ниже 👇"
        ),
        "btn_income": "💰 Доход",
        "btn_expense": "💳 Расход",
        "btn_stats": "📊 Статистика и отчёты",
        "btn_balance": "💰 Мой баланс",
        "btn_history": "🕒 История операций",
        "btn_help": "ℹ️ Помощь",
        "btn_lang": "🌐 Til / Язык",
        "btn_cancel": "❌ Отмена",
        "placeholder": "Выберите Доход или Расход, напишите или отправьте голос...",
        "income_prompt": (
            "🟢 <b>Выбран раздел «Доход»!</b>\n\n"
            "<b>Напишите</b> сумму и источник (например: <i>'150 000 зарплата'</i> или <i>'50k фриланс'</i>)\n"
            "или отправьте 🎙 <b>голосовое сообщение</b>:"
        ),
        "expense_prompt": (
            "🔴 <b>Выбран раздел «Расход»!</b>\n\n"
            "<b>Напишите</b> сумму и назначение (например: <i>'25 000 обед'</i> или <i>'15k такси'</i>)\n"
            "или отправьте 🎙 <b>голосовое сообщение</b>:"
        ),
        "voice_processing": "🎙 <i>Слушаю и анализирую ваше голосовое сообщение...</i>",
        "voice_no_speech": (
            "🎙 <b>Голос не распознан.</b>\n\n"
            "Пожалуйста, говорите ближе к микрофону или отправьте текст "
            "(например: <i>'25 000 обед'</i>)."
        ),
        "voice_no_amount": (
            "🎙 <b>Распознано:</b> «<i>{transcript}</i>»\n\n"
            "⚠️ В сообщении не найдена сумма.\n"
            "Пожалуйста, укажите также сумму (например: <i>'Обед 25 тысяч'</i>)."
        ),
        "voice_error": "⚠️ Ошибка при анализе голосового сообщения:\n<code>{error}</code>",
        "heard": "Распознано",
        "summary_title": "Распознанные данные:",
        "type_label": "Тип",
        "income_name": "Доход",
        "expense_name": "Расход",
        "amount_label": "Сумма",
        "category_label": "Категория",
        "comment_label": "Описание/Цель",
        "is_correct_question": "Данные верны?",
        "which_part_question": "Что вы хотите изменить?",
        "btn_done": "✅ Done — Подтвердить",
        "btn_fix": "✏️ Fix — Исправить",
        "btn_edit_amount": "💵 Изменить сумму",
        "btn_edit_type": "🔄 Изменить Доход/Расход",
        "btn_edit_comment": "📝 Изменить описание",
        "btn_ready_save": "✅ Готово — Сохранить",
        "saved_success": "успешно сохранено!",
        "current_balance": "Текущий чистый баланс:",
        "cancelled": "Действие отменено.",
        "expired": "⏳ Эта запись устарела или уже сохранена.",
        "edit_amount_prompt": "💵 Текущая сумма: <b>{amount}</b>\n\nВведите новую сумму (например: <code>50000</code> или <code>50k</code>):",
        "amount_updated": "Сумма обновлена:",
        "edit_type_prompt": "🔄 Текущий тип: <b>{type}</b>\n\nВыберите нужный тип:",
        "type_updated": "Тип обновлен:",
        "edit_comment_prompt": "📝 Текущее описание: <b>{comment}</b>\n\nВведите новое описание или назначение:",
        "comment_updated": "Описание обновлено:",
        "balance_title": "💳 <b>Ваш общий финансовый баланс:</b>",
        "total_income": "Всего доходов",
        "total_expense": "Всего расходов",
        "net_savings": "Чистые накопления",
        "report_prompt": "📊 <b>За какой период показать отчёт?</b>\n\nВыберите период ниже:",
        "report_today": "📅 Сегодня",
        "report_yesterday": "📆 Вчера",
        "report_week": "🗓 Последние 7 дней",
        "report_month": "📊 Этот месяц",
        "report_last_month": "📈 Прошлый месяц",
        "report_all": "💰 Общий баланс",
        "no_history": "🕒 У вас пока нет истории операций.",
        "recent_history_title": "🕒 <b>Ваши последние операции:</b>",
        "delete_action": "удалить",
        "deleted_success": "Операция удалена.",
        "help_text": (
            "💡 <b>Руководство по использованию бота</b>\n\n"
            "<b>1. Ввод дохода или расхода:</b>\n"
            "• Нажмите <b>💰 Доход</b> или <b>💳 Расход</b> внизу;\n"
            "• Напишите сумму и цель (например: <code>25 000 обед</code>) или отправьте 🎙 <b>голосовое сообщение</b>;\n"
            "• Нажмите <b>✅ Done</b> для подтверждения или <b>✏️ Fix</b> для исправления!\n\n"
            "<b>2. Голосовые сообщения:</b>\n"
            "Говорите свободно на русском или узбекском языке — ИИ автоматически распознает сумму и назначение!\n\n"
            "<b>3. Быстрая запись:</b>\n"
            "• <code>-15000 обед</code> или <code>-20k такси</code>\n"
            "• <code>+500000 зарплата</code> или <code>+100k фриланс</code>\n\n"
            "<b>4. Смена языка:</b>\n"
            "• Кнопка <b>🌐 Til / Язык</b> внизу позволяет сменить язык в любой момент."
        ),
    }
}


def t(key: str, lang: str = "uz", **kwargs) -> str:
    """Tilga mos matnni olish"""
    lang_dict = MESSAGES.get(lang, MESSAGES["uz"])
    template = lang_dict.get(key, MESSAGES["uz"].get(key, key))
    if kwargs:
        return template.format(**kwargs)
    return template
