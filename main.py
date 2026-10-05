import os
import asyncio
import logging
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import BOT_TOKEN
import database as db
from handlers import common, voice, transactions, reports, history

# Windows konsoli uchun UTF-8 kodlashni yoqish
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Loglarni sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

WEBHOOK_PATH = "/webhook"
BASE_WEBHOOK_URL = (os.getenv("RENDER_EXTERNAL_URL") or os.getenv("WEBHOOK_URL") or "").rstrip("/")


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish / Запустить"),
        BotCommand(command="excel", description="Oylik Excel hisobot / Скачать Excel-отчет"),
        BotCommand(command="language", description="Tilni tanlash / Выбрать язык"),
        BotCommand(command="restart", description="Botni qayta yuklash / Перезагрузить"),
        BotCommand(command="help", description="Qo'llanma va yordam / Помощь"),
        BotCommand(command="cancel", description="Bekor qilish / Отмена"),
    ]
    await bot.set_my_commands(commands)


async def handle_health(request):
    from monthly_scheduler import get_tashkent_now
    now = get_tashkent_now()
    return web.json_response({
        "status": "ok",
        "service": "finance-telegram-bot",
        "webhook_url": f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}" if BASE_WEBHOOK_URL else "polling",
        "tashkent_time": now.strftime("%Y-%m-%d %H:%M:%S")
    })


async def on_startup(bot: Bot):
    await db.init_db()
    await set_bot_commands(bot)

    # Har oyning oxirgi kuni soat 22:00 da hisobot jo'natuvchi schedulerni orqa fonda yoqish
    from monthly_scheduler import start_monthly_scheduler
    asyncio.create_task(start_monthly_scheduler(bot))

    if BASE_WEBHOOK_URL:
        webhook_url = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"
        logger.info(f"Webhook o'rnatilmoqda: {webhook_url}")
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=False,
            allowed_updates=["message", "callback_query"]
        )
        logger.info("Webhook muvaffaqiyatli o'rnatildi!")


async def on_shutdown(bot: Bot):
    # Webhookni o'chirmaymiz, chunki server uyquga ketganida
    # yangi xabar kelishi bilan Render serverni avtomatik uyg'otishi kerak.
    logger.info("Bot serveri to'xtatildi (Webhook faol saqlab qolindi).")


def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("XATOLIK: .env faylida BOT_TOKEN topilmadi!")
        return

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Routerlarni ulash
    dp.include_router(common.router)
    dp.include_router(reports.router)
    dp.include_router(history.router)
    dp.include_router(transactions.router)
    dp.include_router(voice.router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # 1. Render.com da WEBHOOK orqali ishlash
    if BASE_WEBHOOK_URL:
        logger.info(f"Render.com Webhook rejimi faollashdi: {BASE_WEBHOOK_URL}")
        app = web.Application()
        app.router.add_get("/", handle_health)
        app.router.add_get("/health", handle_health)

        SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        ).register(app, path=WEBHOOK_PATH)

        setup_application(app, dp, bot=bot)

        port = int(os.getenv("PORT", 8080))
        web.run_app(app, host="0.0.0.0", port=port)

    # 2. Mahalliy kompyuterda POLLING orqali ishlash
    else:
        logger.info("Mahalliy kompyuter: Polling rejimi faollashdi...")
        async def run_polling():
            await db.init_db()
            await set_bot_commands(bot)
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Bot muvaffaqiyatli ishga tushdi va xabarlarni kutmoqda...")
            try:
                await dp.start_polling(bot)
            finally:
                await bot.session.close()

        asyncio.run(run_polling())


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
