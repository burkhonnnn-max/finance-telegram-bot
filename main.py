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
BASE_WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="restart", description="Botni qayta yuklash / yangilash"),
        BotCommand(command="help", description="Qo'llanma va yordam"),
        BotCommand(command="cancel", description="Joriy amalni bekor qilish"),
    ]
    await bot.set_my_commands(commands)


async def handle_health(request):
    return web.Response(text="OK - Finance Bot is alive and healthy!")


async def on_startup(bot: Bot):
    await db.init_db()
    await set_bot_commands(bot)
    if BASE_WEBHOOK_URL:
        webhook_url = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"
        logger.info(f"Webhook o'rnatilmoqda: {webhook_url}")
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        logger.info("Webhook muvaffaqiyatli o'rnatildi!")


async def on_shutdown(bot: Bot):
    if BASE_WEBHOOK_URL:
        logger.info("Webhook o'chirilmoqda...")
        await bot.delete_webhook()
        logger.info("Webhook o'chirildi.")


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
    dp.include_router(voice.router)
    dp.include_router(reports.router)
    dp.include_router(history.router)
    dp.include_router(transactions.router)

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
