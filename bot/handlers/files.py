from aiogram import Router, F
from aiogram.types import CallbackQuery
from bot.services.api_client import APIClient

router = Router()
api = APIClient()

@router.callback_query(F.data.startswith("file:update:"))
async def on_file_update(callback: CallbackQuery):
    tg_id = callback.from_user.id
    await callback.answer("Обновляю куки на сервере...")

    try:
        file_obj = await api.regen_user_file(tg_id)
        updated_at = file_obj.get("updated_at") or "нет данных"

        await callback.message.answer(
            f"✅ Куки перегенерированы, получите новые в профиле!\n\n📅 Последнее обновление: {updated_at}"
        )

        await callback.message.delete()

    except Exception as e:
        await callback.message.answer(
            f"❌ Ошибка при обновлении куков: {e}", parse_mode=None
        )
