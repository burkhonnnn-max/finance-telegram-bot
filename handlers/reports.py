from datetime import datetime, timedelta
import calendar
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

import database as db
from keyboards import get_report_period_keyboard, get_main_keyboard
from utils import format_money, generate_progress_bar
from locales import t, localize_category

router = Router()


@router.message(F.text.in_({"💰 Mening balansim", "💵 Mening balansim", "💰 Мой баланс"}), StateFilter("*"))
async def show_balance(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    balance_info = await db.get_balance(user_id)

    total_income = balance_info["income"]
    total_expense = balance_info["expense"]
    current_balance = balance_info["balance"]

    status_icon = "🟢" if current_balance >= 0 else "🔴"

    if user_lang == "ru":
        text = (
            f"💳 <b>Ваш общий финансовый баланс:</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🟢 <b>Всего доходов:</b> +{format_money(total_income)}\n"
            f"🔴 <b>Всего расходов:</b> -{format_money(total_expense)}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{status_icon} <b>Чистые накопления:</b> <b>{format_money(current_balance)}</b>\n\n"
            f"Для подробной аналитики перейдите в <b>'📊 Статистика и отчёты'</b>."
        )
    else:
        text = (
            f"💳 <b>Sizning umumiy moliyaviy balansingiz:</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🟢 <b>Jami kirim:</b> +{format_money(total_income)}\n"
            f"🔴 <b>Jami chiqim:</b> -{format_money(total_expense)}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{status_icon} <b>Sof jamg'arma:</b> <b>{format_money(current_balance)}</b>\n\n"
            f"Batafsil statistika ko'rish uchun <b>'📊 Statistika & Hisobot'</b> bo'limiga o'ting."
        )

    await message.answer(text, reply_markup=get_main_keyboard(user_lang), parse_mode="HTML")


@router.message(F.text.in_({"📊 Statistika & Hisobot", "📊 Statistika", "📊 Статистика и отчёты", "📊 Статистика"}), StateFilter("*"))
async def select_report_period(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"

    await message.answer(
        t("report_prompt", user_lang),
        reply_markup=get_report_period_keyboard(user_lang),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("report_"))
async def process_report_period(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_lang = (await db.get_user_language(user_id)) or "uz"
    action = callback.data
    now = datetime.now()

    title = ""
    start_date = ""
    end_date = ""

    if action == "report_today":
        title = "📅 Сегодняшний отчёт" if user_lang == "ru" else "📅 Bugungi hisobot"
        start_date = now.strftime("%Y-%m-%d 00:00:00")
        end_date = now.strftime("%Y-%m-%d 23:59:59")
    elif action == "report_yesterday":
        yesterday = now - timedelta(days=1)
        title = "📆 Вчерашний отчёт" if user_lang == "ru" else "📆 Kechagi hisobot"
        start_date = yesterday.strftime("%Y-%m-%d 00:00:00")
        end_date = yesterday.strftime("%Y-%m-%d 23:59:59")
    elif action == "report_week":
        week_ago = now - timedelta(days=7)
        title = "🗓 Отчёт за последние 7 дней" if user_lang == "ru" else "🗓 Oxirgi 7 kunlik hisobot"
        start_date = week_ago.strftime("%Y-%m-%d 00:00:00")
        end_date = now.strftime("%Y-%m-%d 23:59:59")
    elif action == "report_month":
        title = f"📊 Отчёт за этот месяц ({now.strftime('%m.%Y')})" if user_lang == "ru" else f"📊 Joriy oy hisoboti ({now.strftime('%m.%Y')})"
        start_date = now.strftime("%Y-%m-01 00:00:00")
        _, last_day = calendar.monthrange(now.year, now.month)
        end_date = f"{now.year}-{now.month:02d}-{last_day:02d} 23:59:59"
    elif action == "report_last_month":
        first_of_month = now.replace(day=1)
        last_month_end = first_of_month - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        title = f"📈 Отчёт за прошлый месяц ({last_month_start.strftime('%m.%Y')})" if user_lang == "ru" else f"📈 O'tgan oy hisoboti ({last_month_start.strftime('%m.%Y')})"
        start_date = last_month_start.strftime("%Y-%m-01 00:00:00")
        end_date = last_month_end.strftime("%Y-%m-%d 23:59:59")
    elif action == "report_all":
        title = "💰 Общий финансовый итог" if user_lang == "ru" else "💰 Barcha davrlardagi umumiy hisobot"
        start_date = "2000-01-01 00:00:00"
        end_date = "2099-12-31 23:59:59"

    stats = await db.get_stats_for_period(user_id, start_date, end_date)

    total_income = stats["income"]
    total_expense = stats["expense"]
    difference = stats["difference"]

    diff_icon = "🟢 +" if difference >= 0 else "🔴 "

    if user_lang == "ru":
        text = (
            f"<b>{title}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🟢 <b>Доход:</b> +{format_money(total_income)}\n"
            f"🔴 <b>Расход:</b> -{format_money(total_expense)}\n"
            f"⚖️ <b>Разница:</b> {diff_icon}{format_money(difference)}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
        )
    else:
        text = (
            f"<b>{title}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🟢 <b>Kirim:</b> +{format_money(total_income)}\n"
            f"🔴 <b>Chiqim:</b> -{format_money(total_expense)}\n"
            f"⚖️ <b>Farq (Sof foyda):</b> {diff_icon}{format_money(difference)}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
        )

    # Chiqimlar toifasi
    if stats["categories_expense"]:
        cat_exp_title = "\n📂 <b>Расходы по категориям:</b>\n" if user_lang == "ru" else "\n📂 <b>Chiqimlar toifalar bo'yicha:</b>\n"
        text += cat_exp_title
        for item in stats["categories_expense"]:
            bar = generate_progress_bar(item["percentage"], length=6)
            cat_name = localize_category(item['category'], user_lang)
            text += (
                f"• {cat_name}: <b>{format_money(item['total'])}</b>\n"
                f"  <code>{bar}</code> {item['percentage']}%\n"
            )

    # Kirimlar toifasi
    if stats["categories_income"]:
        cat_inc_title = "\n📂 <b>Доходы по категориям:</b>\n" if user_lang == "ru" else "\n📂 <b>Kirimlar toifalar bo'yicha:</b>\n"
        text += cat_inc_title
        for item in stats["categories_income"]:
            bar = generate_progress_bar(item["percentage"], length=6)
            cat_name = localize_category(item['category'], user_lang)
            text += (
                f"• {cat_name}: <b>{format_money(item['total'])}</b>\n"
                f"  <code>{bar}</code> {item['percentage']}%\n"
            )

    if not stats["categories_expense"] and not stats["categories_income"]:
        empty_note = "\n<i>В этот период операций не совершалось.</i>" if user_lang == "ru" else "\n<i>Ushbu davrda hech qanday operatsiya amalga oshirilmagan.</i>"
        text += empty_note

    await callback.message.edit_text(
        text,
        reply_markup=get_report_period_keyboard(user_lang),
        parse_mode="HTML"
    )
    await callback.answer()
