import asyncio
import uvicorn
import logging
from aiogram import Dispatcher
from bot.loader import bot, dp
from bot.handlers import files, start, subscription, profile, ai, image_generation, topup
from bot.handlers import keyboard_update
from bot.api import app as fastapi_app

# Настройка логирования для бота
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


async def run_bot():
    dp.include_router(start.router)
    dp.include_router(subscription.router)
    dp.include_router(profile.router)
    dp.include_router(ai.router)
    dp.include_router(files.router)
    dp.include_router(image_generation.router)
    dp.include_router(topup.router)
    dp.include_router(keyboard_update.router)
    # dp.include_router(referral.router)
    # dp.include_router(faq.router)
    # dp.include_router(access_file.router)

    await dp.start_polling(bot)


async def run_api():
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8001, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await asyncio.gather(run_bot(), run_api())


if __name__ == "__main__":
    asyncio.run(main())
