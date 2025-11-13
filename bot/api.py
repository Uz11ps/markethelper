from fastapi import FastAPI
from bot.loader import bot

app = FastAPI()


@app.post("/notify")
async def notify(payload: dict):
    """
    Принимает уведомления от backend и отправляет юзерам в Telegram
    """
    tg_id = payload.get("tg_id")
    message = payload.get("message")
    if tg_id and message:
        await bot.send_message(chat_id=tg_id, text=message)
    return {"ok": True}


@app.post("/broadcast")
async def broadcast(payload: dict):
    """
    Принимает сообщение для рассылки от backend и отправляет в Telegram
    Поддерживает как одиночную отправку (tg_id), так и массовую (user_ids)
    """
    message = payload.get("message")

    if not message:
        return {"ok": False, "error": "Missing message"}

    # Поддержка старого формата (один tg_id)
    tg_id = payload.get("tg_id")
    # Поддержка нового формата (список user_ids)
    user_ids = payload.get("user_ids", [])

    if tg_id:
        user_ids = [tg_id]

    if not user_ids:
        return {"ok": False, "error": "Missing tg_id or user_ids"}

    success_count = 0
    failed_count = 0
    errors = []

    for user_id in user_ids:
        try:
            await bot.send_message(chat_id=user_id, text=message)
            success_count += 1
        except Exception as e:
            failed_count += 1
            errors.append({"user_id": user_id, "error": str(e)})

    return {
        "ok": True,
        "success_count": success_count,
        "failed_count": failed_count,
        "errors": errors[:10]  # Возвращаем первые 10 ошибок
    }
