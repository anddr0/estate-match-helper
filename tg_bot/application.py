import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from loguru import logger

from tg_bot.handlers import router
from utils.logger import setup_logging


async def run_bot() -> None:
    load_dotenv()
    setup_logging()

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not configured")

    logger.info("Запуск бота...")
    bot = Bot(token=token)
    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot)
