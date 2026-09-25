import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from config import BOT_TOKEN
import database as db
from handlers import common, transactions, reports, history, voice

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


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Botni qayta ishga tushirish"),
        BotCommand(command="help", description="Qo'llanma va yordam"),
        BotCommand(command="cancel", description="Joriy amalni bekor qilish"),
    ]
    await bot.set_my_commands(commands)


import os
from aiohttp import web

async def handle_health(request):
    return web.Response(text="OK - Finance Bot is alive!")


async def start_web_server():
    port = int(os.getenv("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", handle_health)
    app.router.add_get("/health", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health check web server {port}-portda ishga tushdi (Render uchun).")
    return runner


async def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error(
            "XATOLIK: .env faylida BOT_TOKEN topilmadi!\n"
            "Iltimos, Telegram'dagi @BotFather'dan bot ochib, uning tokenini .env faylidagi BOT_TOKEN qatoriga yozing."
        )
        return

    # Baza jadvallarini ishga tushirish
    logger.info("Ma'lumotlar bazasi tekshirilmoqda...")
    await db.init_db()

    # Bot va Dispatcher obyektlari
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Routerlarni ulash
    dp.include_router(common.router)
    dp.include_router(transactions.router)
    dp.include_router(voice.router)
    dp.include_router(reports.router)
    dp.include_router(history.router)

    # Buyruqlar menyusini o'rnatish
    await set_bot_commands(bot)

    web_runner = None
    # Render.com yoki boshqa bulutli serverlar uchun portni tinglash
    if os.getenv("PORT"):
        web_runner = await start_web_server()

    logger.info("Bot muvaffaqiyatli ishga tushdi va xabarlarni kutmoqda...")
    try:
        # Eski xabarlarni (pending updates) o'chirib tashlash
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        if web_runner:
            await web_runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
