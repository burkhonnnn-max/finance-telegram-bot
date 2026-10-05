# -*- coding: utf-8 -*-
"""
Oylik avtomatik hisobot jo'natuvchi va rejalashtiruvchi (Scheduler) modul.
Har oyning oxirgi kuni soat 22:00 da (Toshkent vaqti bilan, UTC+5) barcha foydalanuvchilarga
avtomatik tarzda oylik Excel (.xlsx) hisobotini generatsiya qilib jo'natadi.
"""

import asyncio
import calendar
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from aiogram import Bot
from aiogram.types import BufferedInputFile

import database as db
from excel_generator import create_monthly_excel_report, MONTHS_UZ, MONTHS_RU
from utils import format_money

logger = logging.getLogger(__name__)

# O'zbekiston vaqti (Toshkent, UTC+5)
UZB_TZ = timezone(timedelta(hours=5))


def get_tashkent_now() -> datetime:
    """Toshkent vaqti bo'yicha joriy vaqtni olish (UTC+5)"""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Asia/Tashkent"))
    except Exception:
        return datetime.now(UZB_TZ)


async def send_user_excel_report(
    bot: Bot,
    user_id: int,
    user_name: str,
    user_lang: str,
    year: int,
    month: int,
    is_auto: bool = True
) -> bool:
    """
    Muayyan foydalanuvchiga oylik Excel hisobotini generatsiya qilib Telegram orqali yuborish.
    """
    try:
        import calendar
        _, last_day = calendar.monthrange(year, month)
        start_date = f"{year}-{month:02d}-01 00:00:00"
        end_date = f"{year}-{month:02d}-{last_day:02d} 23:59:59"

        stats = await db.get_stats_for_period(user_id, start_date, end_date)
        transactions = await db.get_month_transactions(user_id, year, month)

        # Agar avtomatik jo'natish bo'lsa va foydalanuvchida umuman amal bo'lmasa, jo'natmaslik ham mumkin
        if is_auto and not transactions and stats.get("income", 0) == 0 and stats.get("expense", 0) == 0:
            logger.info(f"Foydalanuvchi {user_id} da {year}-{month:02d} uchun amallar yo'q, o'tkazib yuborildi.")
            return False

        # Excel faylini generatsiya qilish
        excel_bytes = create_monthly_excel_report(
            user_name=user_name,
            user_lang=user_lang,
            year=year,
            month=month,
            stats=stats,
            transactions=transactions
        )

        filename = f"moliya_hisoboti_{year}_{month:02d}.xlsx"
        is_ru = (user_lang == "ru")
        month_name = MONTHS_RU.get(month, "") if is_ru else MONTHS_UZ.get(month, "")

        income = stats.get("income", 0.0)
        expense = stats.get("expense", 0.0)
        diff = stats.get("difference", 0.0)
        ops_count = len(transactions)

        if is_ru:
            title_prefix = "🔔 <b>Ежемесячный автоматический отчёт!</b>\n" if is_auto else ""
            caption = (
                f"{title_prefix}"
                f"📊 <b>Ваш финансовый отчёт за {month_name} {year} готов!</b> 📥\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🟢 <b>Всего доходов:</b> +{format_money(income)}\n"
                f"🔴 <b>Всего расходов:</b> -{format_money(expense)}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 <b>Чистый остаток:</b> <b>{format_money(diff)}</b>\n"
                f"📝 <b>Всего операций:</b> {ops_count}\n\n"
                f"📎 <i>Подробная аналитика и все ваши записи находятся в прикреплённом Excel (.xlsx) файле.</i>"
            )
        else:
            title_prefix = "🔔 <b>Oylik avtomatik hisobot!</b>\n" if is_auto else ""
            caption = (
                f"{title_prefix}"
                f"📊 <b>{year}-yil {month_name} oyi uchun moliyaviy hisobotingiz tayyor!</b> 📥\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🟢 <b>Jami kirim:</b> +{format_money(income)}\n"
                f"🔴 <b>Jami chiqim:</b> -{format_money(expense)}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 <b>Sof jamg'arma:</b> <b>{format_money(diff)}</b>\n"
                f"📝 <b>Amallar soni:</b> {ops_count} ta\n\n"
                f"📎 <i>Barcha yozuvlar va toifalar bo'yicha batafsil ma'lumot ilova qilingan Excel (.xlsx) faylida jamlangan.</i>"
            )

        document = BufferedInputFile(excel_bytes, filename=filename)
        await bot.send_document(
            chat_id=user_id,
            document=document,
            caption=caption,
            parse_mode="HTML"
        )
        logger.info(f"Foydalanuvchi {user_id} ga {year}-{month:02d} hisoboti muvaffaqiyatli yuborildi.")
        return True

    except Exception as e:
        logger.error(f"Foydalanuvchi {user_id} ga hisobot yuborishda xatolik: {e}")
        return False


async def check_and_send_monthly_reports(bot: Bot):
    """
    Toshkent vaqti bilan har oyning oxirgi kuni soat 22:00 da hisobot jo'natish tekshiruvi.
    """
    now = get_tashkent_now()
    year = now.year
    month = now.month
    day = now.day
    hour = now.hour

    _, last_day = calendar.monthrange(year, month)
    year_month = f"{year}-{month:02d}"

    # Shart: Oyning oxirgi kuni va soat 22:00 yoki undan keyin (lekin o'sha kuni 23:59 gacha)
    if day == last_day and hour >= 22:
        # Ushbu oy uchun hisobot allaqachon yuborilganmi?
        already_sent = await db.is_monthly_report_sent(year_month)
        if not already_sent:
            logger.info(f"🚀 Oylik hisobot jo'natish boshlandi: {year_month} (Vaqt: {now.strftime('%Y-%m-%d %H:%M:%S')})")
            users = await db.get_all_users()
            sent_count = 0

            for u in users:
                u_id = u["user_id"]
                u_name = u.get("full_name") or "Foydalanuvchi"
                u_lang = u.get("language") or "uz"
                
                success = await send_user_excel_report(
                    bot=bot,
                    user_id=u_id,
                    user_name=u_name,
                    user_lang=u_lang,
                    year=year,
                    month=month,
                    is_auto=True
                )
                if success:
                    sent_count += 1
                await asyncio.sleep(0.3)  # Telegram limits

            await db.mark_monthly_report_sent(year_month, sent_count)
            logger.info(f"✅ Oylik hisobot {sent_count} ta foydalanuvchiga yuborildi va bazaga belgilandi.")


async def start_monthly_scheduler(bot: Bot):
    """
    Orqa fonda uzluksiz ishlovchi scheduler vazifasi (har 30 soniyada tekshiradi).
    """
    logger.info("📅 Oylik avtomatik hisobot scheduleri ishga tushdi (Har oy oxirgi kuni 22:00 da).")
    while True:
        try:
            await check_and_send_monthly_reports(bot)
        except Exception as e:
            logger.error(f"Scheduler xatoligi: {e}")
        await asyncio.sleep(30)
