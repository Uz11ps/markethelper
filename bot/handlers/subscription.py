from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from bot.keyboards import subscription
from bot.services.api_client import APIClient

router = Router()
api = APIClient()


@router.message(F.text == "🛒Тарифы и подписка")
async def choose_tariff(message: Message):
    await message.answer("Выберите тариф:", reply_markup=subscription.tariffs_kb())


@router.callback_query(F.data.startswith("tariff:"))
async def choose_duration(callback: CallbackQuery):
    tariff_code = callback.data.split(":")[1]
    await callback.message.edit_text(
        "Выберите срок подписки:",
        reply_markup=subscription.durations_kb(tariff_code)
    )


@router.callback_query(F.data.startswith("duration:"))
async def create_request(callback: CallbackQuery):
    _, tariff_code, months = callback.data.split(":")
    months = int(months)

    result = await api.create_request(
        tg_id=callback.from_user.id,
        tariff_code=tariff_code,
        duration_months=months
    )

    await callback.message.edit_text(
        "✅ Ваша заявка принята!\n"
        "Администратор скоро свяжется с вами для подтверждения."
    )
