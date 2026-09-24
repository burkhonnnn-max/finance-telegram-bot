from datetime import datetime, timedelta
import calendar
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from keyboards import get_report_period_keyboard, get_main_keyboard
from utils import format_money, generate_progress_bar

router = Router()


@router.message(F.text == "💰 Mening balansim")
async def show_balance(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    balance_info = await db.get_balance(user_id)

    total_income = balance_info["income"]
    total_expense = balance_info["expense"]
    current_balance = balance_info["balance"]

    status_icon = "🟢" if current_balance >= 0 else "🔴"

    text = (
        f"💳 <b>Sizning umumiy moliyaviy balansingiz:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 <b>Jami kirim:</b> +{format_money(total_income)}\n"
        f"🔴 <b>Jami chiqim:</b> -{format_money(total_expense)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{status_icon} <b>Sof jamg'arma:</b> <b>{format_money(current_balance)}</b>\n\n"
        f"Batafsil statistika ko'rish uchun <b>'📊 Statistika & Hisobot'</b> bo'limiga o'ting."
    )
    await message.answer(text, reply_markup=get_main_keyboard(), parse_mode="HTML")


@router.message(F.text == "📊 Statistika & Hisobot")
async def select_report_period(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📊 <b>Qaysi davr bo'yicha hisobot ko'rmoqchisiz?</b>\n\n"
        "Quyidagi tugmalardan birini tanlang:",
        reply_markup=get_report_period_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("report_"))
async def process_report_period(callback: CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data
    now = datetime.now()

    title = ""
    start_date = ""
    end_date = ""

    if action == "report_today":
        title = "📅 Bugungi hisobot"
        start_date = now.strftime("%Y-%m-%d 00:00:00")
        end_date = now.strftime("%Y-%m-%d 23:59:59")
    elif action == "report_yesterday":
        yesterday = now - timedelta(days=1)
        title = "📆 Kechagi hisobot"
        start_date = yesterday.strftime("%Y-%m-%d 00:00:00")
        end_date = yesterday.strftime("%Y-%m-%d 23:59:59")
    elif action == "report_week":
        week_ago = now - timedelta(days=7)
        title = "🗓 Oxirgi 7 kunlik hisobot"
        start_date = week_ago.strftime("%Y-%m-%d 00:00:00")
        end_date = now.strftime("%Y-%m-%d 23:59:59")
    elif action == "report_month":
        title = f"📊 Joriy oy hisoboti ({now.strftime('%B %Y')})"
        start_date = now.strftime("%Y-%m-01 00:00:00")
        _, last_day = calendar.monthrange(now.year, now.month)
        end_date = f"{now.year}-{now.month:02d}-{last_day:02d} 23:59:59"
    elif action == "report_last_month":
        first_of_this_month = datetime(now.year, now.month, 1)
        last_day_of_prev_month = first_of_this_month - timedelta(days=1)
        first_day_of_prev_month = datetime(last_day_of_prev_month.year, last_day_of_prev_month.month, 1)
        title = f"📈 O'tgan oy hisoboti ({first_day_of_prev_month.strftime('%B %Y')})"
        start_date = first_day_of_prev_month.strftime("%Y-%m-01 00:00:00")
        _, last_day = calendar.monthrange(first_day_of_prev_month.year, first_day_of_prev_month.month)
        end_date = f"{first_day_of_prev_month.year}-{first_day_of_prev_month.month:02d}-{last_day:02d} 23:59:59"
    elif action == "report_all":
        title = "💰 Barcha davrlar bo'yicha umumiy hisobot"
        start_date = "2000-01-01 00:00:00"
        end_date = "2099-12-31 23:59:59"

    stats = await db.get_stats_for_period(user_id, start_date, end_date)

    income = stats["income"]
    expense = stats["expense"]
    difference = stats["difference"]
    categories_expense = stats["categories_expense"]
    categories_income = stats["categories_income"]

    if income == 0 and expense == 0:
        text = (
            f"<b>{title}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🤷‍♂️ Ushbu davr uchun hali hech qanday kirim yoki chiqim yozilmagan."
        )
        await callback.message.edit_text(text, reply_markup=get_report_period_keyboard(), parse_mode="HTML")
        await callback.answer()
        return

    diff_sign = "🟢 +" if difference >= 0 else "🔴 -"
    text = (
        f"<b>{title}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 <b>Kirim:</b> +{format_money(income)}\n"
        f"🔴 <b>Chiqim:</b> -{format_money(expense)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 <b>Farq (Sof foyda):</b> {diff_sign}{format_money(abs(difference))}\n\n"
    )

    if categories_expense:
        text += "<b>🔻 Chiqimlar toifalar bo'yicha:</b>\n"
        for cat in categories_expense:
            bar = generate_progress_bar(cat["percentage"], length=8)
            text += f"• {cat['category']}: <b>{format_money(cat['total'])}</b> ({cat['percentage']}%) <code>{bar}</code>\n"
        text += "\n"

    if categories_income:
        text += "<b>🔺 Kirimlar toifalar bo'yicha:</b>\n"
        for cat in categories_income:
            bar = generate_progress_bar(cat["percentage"], length=8)
            text += f"• {cat['category']}: <b>{format_money(cat['total'])}</b> ({cat['percentage']}%) <code>{bar}</code>\n"

    await callback.message.edit_text(text, reply_markup=get_report_period_keyboard(), parse_mode="HTML")
    await callback.answer()
