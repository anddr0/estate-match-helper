import asyncio
import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from loguru import logger

import utils.logger  # To initialize logger configuration
from tg_bot.handlers import router

load_dotenv()

async def main():
    logger.info("Запуск бота...")
    bot = Bot(token=os.getenv('BOT_TOKEN'))
    dp = Dispatcher()

    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())