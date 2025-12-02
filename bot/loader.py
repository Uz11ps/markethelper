from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
import bot.config as config

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()
