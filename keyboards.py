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
            KeyboardButton(text="🌐 Til / Язык")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=t("placeholder", lang)
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
