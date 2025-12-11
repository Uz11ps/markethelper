from aiogram import Router, F
from aiogram.types import CallbackQuery
from bot.services.api_client import APIClient

router = Router()
api = APIClient()

# Обработчик file:update удален, так как кнопка "обновить куки" больше не используется
