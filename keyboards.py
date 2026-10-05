from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

# 1. Asosiy doimiy menyu tugmalari
# Foydalanuvchi doimo quyi qismida Kirim va Chiqim tugmalarini ko'rib turadi
def get_main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="💰 Kirim"),
            KeyboardButton(text="💳 Chiqim")
        ],
        [
            KeyboardButton(text="📊 Statistika & Hisobot"),
            KeyboardButton(text="💰 Mening balansim")
        ],
        [
            KeyboardButton(text="🕒 Oxirgi amallar"),
            KeyboardButton(text="ℹ️ Qanday ishlatiladi?")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="💰 Kirim yoki 💳 Chiqimni tanlang, yozing yoki ovoz yuboring..."
    )


# 2. Bekor qilish reply tugmasi
def get_cancel_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💰 Kirim"),
                KeyboardButton(text="💳 Chiqim")
            ],
            [
                KeyboardButton(text="❌ Bekor qilish")
            ]
        ],
        resize_keyboard=True
    )


# 3. Chiqim toifalari (Inline)
EXPENSE_CATEGORIES = [
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

# 4. Kirim toifalari (Inline)
INCOME_CATEGORIES = [
    ("💼 Oylik maosh", "cat_inc_salary"),
    ("💻 Frilans / Biznes", "cat_inc_freelance"),
    ("🎁 Sovg'a / Yordam", "cat_inc_gift"),
    ("🔄 Qarz qaytishi", "cat_inc_debt"),
    ("📈 Savdo / Foyda", "cat_inc_trade"),
    ("📦 Boshqa kirim", "cat_inc_other"),
]


def get_categories_keyboard(tr_type: str) -> InlineKeyboardMarkup:
    items = INCOME_CATEGORIES if tr_type == "income" else EXPENSE_CATEGORIES
    buttons = []
    row = []
    for name, callback_data in items:
        row.append(InlineKeyboardButton(text=name, callback_data=callback_data))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# 5. Izoh bosqichi uchun tugmalar
def get_comment_skip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data="skip_comment"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")
            ]
        ]
    )


# 6. Hisobot davrini tanlash
def get_report_period_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Bugun", callback_data="report_today"),
                InlineKeyboardButton(text="📆 Kecha", callback_data="report_yesterday")
            ],
            [
                InlineKeyboardButton(text="🗓 Oxirgi 7 kun", callback_data="report_week"),
                InlineKeyboardButton(text="📊 Shu oy", callback_data="report_month")
            ],
            [
                InlineKeyboardButton(text="📈 O'tgan oy", callback_data="report_last_month"),
                InlineKeyboardButton(text="💰 Umumiy balans", callback_data="report_all")
            ]
        ]
    )


# 7. Tranzaksiyani o'chirish tasdig'i
def get_delete_transaction_keyboard(transaction_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑 O'chirib tashlash", callback_data=f"del_tx_{transaction_id}")
            ]
        ]
    )


# ===== OVOZLI VA SMS XABARLAR UCHUN TASDIQLASH TUGMALARI =====

def get_confirm_keyboard(pending_id: str) -> InlineKeyboardMarkup:
    """Ma'lumotni tasdiqlash: Done yoki Fix"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Done — Tasdiqlash", callback_data=f"pdone_{pending_id}"),
                InlineKeyboardButton(text="✏️ Fix — To'g'rilash", callback_data=f"pfix_{pending_id}")
            ]
        ]
    )


def get_fix_keyboard(pending_id: str) -> InlineKeyboardMarkup:
    """To'g'rilash bo'limi tugmalari"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💵 Summani o'zgartirish", callback_data=f"pedit_amt_{pending_id}"),
            ],
            [
                InlineKeyboardButton(text="🔄 Kirim/Chiqim o'zgartirish", callback_data=f"pedit_type_{pending_id}"),
            ],
            [
                InlineKeyboardButton(text="📝 Izoh/Maqsad o'zgartirish", callback_data=f"pedit_comm_{pending_id}"),
            ],
            [
                InlineKeyboardButton(text="✅ Tayyor — Saqlash", callback_data=f"pdone_{pending_id}"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"pcancel_{pending_id}"),
            ]
        ]
    )


def get_type_keyboard(pending_id: str) -> InlineKeyboardMarkup:
    """Kirim yoki Chiqim turini tanlash (Inline)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Kirim", callback_data=f"ptype_inc_{pending_id}"),
                InlineKeyboardButton(text="💳 Chiqim", callback_data=f"ptype_exp_{pending_id}"),
            ],
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"pcancel_{pending_id}")
            ]
        ]
    )
