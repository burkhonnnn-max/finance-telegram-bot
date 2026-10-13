from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from locales import (
    t,
    EXPENSE_CATEGORIES_UZ,
    EXPENSE_CATEGORIES_RU,
    INCOME_CATEGORIES_UZ,
)

MENU_BUTTONS = {
    "💰 Kirim", "💳 Chiqim", "➕ Kirim qo'shish", "➖ Chiqim qo'shish",
    "💰 Доход", "💳 Расход", "➕ Доход", "➖ Расход",
    "📊 Statistika & Hisobot", "📊 Statistika", "📊 Статистика и отчёты", "📊 Статистика",
    "💰 Mening balansim", "💵 Mening balansim", "💰 Мой баланс",
    "🕒 Oxirgi amallar", "🕒 История операций",
    "ℹ️ Qanday ishlatiladi?", "ℹ️ Yordam", "ℹ️ Помощь",
    "⚡ Avto", "⚡ Авто", "Avto", "Авто",
    "🌐 Til / Язык",
    "❌ Bekor qilish", "❌ Отмена"
}

# 1. Tilni tanlash inline klaviaturasi
def get_language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="set_lang_uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru")
            ]
        ]
    )


# 2. Asosiy doimiy menyu tugmalari (uz & ru)
def get_main_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    is_ru = (lang == "ru")
    keyboard = [
        [
            KeyboardButton(text=t("btn_income", lang)),
            KeyboardButton(text=t("btn_expense", lang))
        ],
        [
            KeyboardButton(text=t("btn_stats", lang)),
            KeyboardButton(text=t("btn_balance", lang))
        ],
        [
            KeyboardButton(text=t("btn_history", lang)),
            KeyboardButton(text=t("btn_help", lang))
        ],
        [
            KeyboardButton(text="⚡ Avto" if not is_ru else "⚡ Авто")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=t("placeholder", lang)
    )


# 2.1 Telefon raqamni ulashish klaviaturasi
def get_phone_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Telefon raqamni ulashish klaviaturasi (Contact tugmasi va Bekor qilish)"""
    contact_text = "📱 Telefon raqamni ulashish" if lang != "ru" else "📱 Поделиться контактом"
    cancel_text = "❌ Bekor qilish" if lang != "ru" else "❌ Отмена"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=contact_text, request_contact=True)],
            [KeyboardButton(text=cancel_text)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


# 3. Bekor qilish reply tugmasi
def get_cancel_reply_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t("btn_income", lang)),
                KeyboardButton(text=t("btn_expense", lang))
            ],
            [
                KeyboardButton(text=t("btn_cancel", lang))
            ]
        ],
        resize_keyboard=True
    )


# 4. Toifalar klaviaturasi (uz & ru)
def get_categories_keyboard(tr_type: str, lang: str = "uz") -> InlineKeyboardMarkup:
    if lang == "ru":
        items = INCOME_CATEGORIES_RU if tr_type == "income" else EXPENSE_CATEGORIES_RU
    else:
        items = INCOME_CATEGORIES_UZ if tr_type == "income" else EXPENSE_CATEGORIES_UZ

    buttons = []
    row = []
    for name, callback_data in items:
        row.append(InlineKeyboardButton(text=name, callback_data=callback_data))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# 5. Hisobot davrini tanlash (uz & ru)
def get_report_period_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("report_today", lang), callback_data="report_today"),
                InlineKeyboardButton(text=t("report_yesterday", lang), callback_data="report_yesterday")
            ],
            [
                InlineKeyboardButton(text=t("report_week", lang), callback_data="report_week"),
                InlineKeyboardButton(text=t("report_month", lang), callback_data="report_month")
            ],
            [
                InlineKeyboardButton(text=t("report_last_month", lang), callback_data="report_last_month"),
                InlineKeyboardButton(text=t("report_all", lang), callback_data="report_all")
            ],
            [
                InlineKeyboardButton(
                    text="📥 " + ("Скачать Excel (.xlsx)" if lang == "ru" else "Excel hisobot (.xlsx)"),
                    callback_data="report_excel_current"
                )
            ]
        ]
    )


# 6. Tranzaksiyani o'chirish tasdig'i
def get_delete_transaction_keyboard(transaction_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    del_text = "🗑 " + t("delete_action", lang).capitalize()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=del_text, callback_data=f"del_tx_{transaction_id}")
            ]
        ]
    )


# 7. Tasdiqlash: Done yoki Fix
def get_confirm_keyboard(pending_id: str, lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_done", lang), callback_data=f"pdone_{pending_id}"),
                InlineKeyboardButton(text=t("btn_fix", lang), callback_data=f"pfix_{pending_id}")
            ]
        ]
    )


# 8. To'g'rilash (Fix) menyusi tugmalari
def get_fix_keyboard(pending_id: str, lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_edit_amount", lang), callback_data=f"pedit_amt_{pending_id}"),
            ],
            [
                InlineKeyboardButton(text=t("btn_edit_type", lang), callback_data=f"pedit_type_{pending_id}"),
            ],
            [
                InlineKeyboardButton(text=t("btn_edit_comment", lang), callback_data=f"pedit_comm_{pending_id}"),
            ],
            [
                InlineKeyboardButton(text=t("btn_ready_save", lang), callback_data=f"pdone_{pending_id}"),
                InlineKeyboardButton(text=t("btn_cancel", lang), callback_data=f"pcancel_{pending_id}"),
            ]
        ]
    )


# 9. Kirim/Chiqim (Доход/Расход) turini tanlash
def get_type_keyboard(pending_id: str, lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_income", lang), callback_data=f"ptype_inc_{pending_id}"),
                InlineKeyboardButton(text=t("btn_expense", lang), callback_data=f"ptype_exp_{pending_id}"),
            ],
            [
                InlineKeyboardButton(text=t("btn_cancel", lang), callback_data=f"pcancel_{pending_id}")
            ]
        ]
    )


# =========================================================================
# 10. AVTO / TEZKOR SAQLANGAN AMALLAR KLAVIATURALARI
# =========================================================================

def get_template_emoji(name: str, tr_type: str = "expense") -> str:
    """Nomi bo'yicha mos keladigan emojini tanlash"""
    low = (name or "").lower()
    if any(w in low for w in ["avtobus", "автобус", "marshrutka", "маршрутка"]):
        return "🚌"
    if any(w in low for w in ["taxi", "taksi", "такси", "yandex"]):
        return "🚕"
    if any(w in low for w in ["metro", "метро"]):
        return "🚇"
    if any(w in low for w in ["benzin", "zapravka", "propan", "metan", "газ"]):
        return "⛽️"
    if any(w in low for w in ["non", "хлеб", "lepyoshka", "patir"]):
        return "🥖"
    if any(w in low for w in ["kofe", "coffee", "кофе"]):
        return "☕️"
    if any(w in low for w in ["choy", "чай"]):
        return "🫖"
    if any(w in low for w in ["suv", "вода"]):
        return "💧"
    if any(w in low for w in ["tushlik", "ovqat", "osh", "somsa", "lavash", "doner", "еда", "обед"]):
        return "🍽"
    if any(w in low for w in ["sigaret", "сигареты"]):
        return "🚬"
    if any(w in low for w in ["paynet", "telefon", "internet", "интернет"]):
        return "📱"
    if any(w in low for w in ["dori", "apteka", "аптека"]):
        return "💊"
    return "🔴" if tr_type == "expense" else "🟢"


def get_quick_templates_keyboard(templates: list, lang: str = "uz") -> InlineKeyboardMarkup:
    """Foydalanuvchining saqlangan tezkor amallari ro'yxati va boshqaruvi"""
    from utils import format_money
    is_ru = (lang == "ru")
    rows = []

    # 1. Shablon tugmalari
    tpl_buttons = []
    for tpl in templates:
        emoji = get_template_emoji(tpl.get("name", ""), tpl.get("type", "expense"))
        amt_str = format_money(tpl.get("amount", 0), lang=lang)
        name = tpl.get("name", "Amal")
        btn_text = f"{emoji} {name} ({amt_str})"
        tpl_buttons.append(InlineKeyboardButton(text=btn_text, callback_data=f"quick_run_{tpl['id']}"))

    # Tugmalarni tartiblash: agar uzun bo'lsa 1 tadan, qisqa bo'lsa 2 tadan
    current_row = []
    for btn in tpl_buttons:
        if len(btn.text) > 22 or len(current_row) == 2:
            if current_row:
                rows.append(current_row)
                current_row = []
        current_row.append(btn)
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)

    # 2. Yangi qo'shish va boshqarish tugmalari
    add_text = "➕ Yangi qo'shish" if not is_ru else "➕ Добавить"
    manage_text = "⚙️ O'chirish" if not is_ru else "⚙️ Удалить"
    close_text = "❌ Yopish" if not is_ru else "❌ Закрыть"

    if templates:
        rows.append([
            InlineKeyboardButton(text=add_text, callback_data="quick_add_new"),
            InlineKeyboardButton(text=manage_text, callback_data="quick_manage")
        ])
    else:
        add_first = "➕ Yangi amal qo'shish" if not is_ru else "➕ Добавить операцию"
        rows.append([InlineKeyboardButton(text=add_first, callback_data="quick_add_new")])

    rows.append([InlineKeyboardButton(text=close_text, callback_data="quick_close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_quick_manage_keyboard(templates: list, lang: str = "uz") -> InlineKeyboardMarkup:
    """Saqlangan amallarni bittalab o'chirish klaviaturasi"""
    from utils import format_money
    is_ru = (lang == "ru")
    rows = []

    for tpl in templates:
        emoji = get_template_emoji(tpl.get("name", ""), tpl.get("type", "expense"))
        amt_str = format_money(tpl.get("amount", 0), lang=lang)
        name = tpl.get("name", "Amal")
        del_text = f"🗑 {emoji} {name} ({amt_str})"
        rows.append([InlineKeyboardButton(text=del_text, callback_data=f"quick_del_{tpl['id']}")])

    back_text = "⬅️ Ortga" if not is_ru else "⬅️ Назад"
    rows.append([InlineKeyboardButton(text=back_text, callback_data="quick_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_quick_cancel_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Yangi amal qo'shishni bekor qilish tugmasi"""
    cancel_text = "❌ Bekor qilish" if lang != "ru" else "❌ Отмена"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=cancel_text, callback_data="quick_cancel_add")]
    ])
