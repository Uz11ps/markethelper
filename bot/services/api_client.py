import aiohttp
import json
from typing import Optional
from bot.config import BACKEND_URL


class APIClientError(Exception):
    """Базовая ошибка API клиента"""


class InsufficientTokensError(APIClientError):
    """Недостаточно токенов"""


class APIClient:
    def __init__(self):
        self.base_url = BACKEND_URL

    async def _handle_response(self, resp: aiohttp.ClientResponse):
        text = await resp.text()
        if resp.status >= 400:
            detail = text
            try:
                data = json.loads(text)
                # Извлекаем detail из ответа
                if isinstance(data, dict):
                    detail = data.get("detail", data.get("message", str(data)))
                else:
                    detail = str(data)
            except Exception:
                detail = text
            
            # Улучшаем сообщения об ошибках для пользователя
            if resp.status == 402:
                raise InsufficientTokensError(detail)
            elif resp.status == 404:
                raise APIClientError(f"Не найдено: {detail}")
            elif resp.status == 500:
                # Для 500 ошибок показываем детали из ответа, если они есть
                if detail and detail != text:
                    # Если удалось распарсить JSON, показываем детали
                    raise APIClientError(detail)
                else:
                    # Иначе показываем общее сообщение
                    raise APIClientError("Внутренняя ошибка сервера")
            else:
                raise APIClientError(f"Ошибка {resp.status}: {detail}")
        try:
            return json.loads(text) if text else {}
        except Exception:
            return {}

    async def create_user(self, tg_id: int, username: str | None, full_name: str | None):
        url = f"{self.base_url}/api/admin/users/"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={
                "tg_id": tg_id,
                "username": username,
                "full_name": full_name,
            }) as resp:
                return await self._handle_response(resp)

    async def get_user(self, tg_id: int):
        url = f"{self.base_url}/api/admin/users/by_tg/{tg_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await self._handle_response(resp)

    async def create_request(
        self, 
        tg_id: int, 
        tariff_code: str, 
        duration_months: int,
        subscription_type: str = "group",
        group_id: Optional[int] = None,
        user_email: Optional[str] = None
    ):
        url = f"{self.base_url}/api/admin/requests/"
        payload = {
            "tg_id": tg_id,
            "tariff_code": tariff_code,
            "duration_months": duration_months,
            "subscription_type": subscription_type,
        }
        # Для складчины group_id может быть None - админ назначит группу при одобрении
        # Включаем group_id в payload только если он явно указан (не None)
        if group_id is not None:
            payload["group_id"] = group_id
        if user_email:
            payload["user_email"] = user_email
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                return await self._handle_response(resp)
    
    async def get_groups(self):
        """Получить список групп доступа"""
        url = f"{self.base_url}/api/groups/"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await self._handle_response(resp)

    async def get_profile(
        self,
        tg_id: int,
        *,
        username: str | None = None,
        full_name: str | None = None,
    ):
        """Возвращает профиль, создавая пользователя при его отсутствии."""
        url = f"{self.base_url}/api/profile/{tg_id}"

        async def _request():
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    return await self._handle_response(resp)

        try:
            return await _request()
        except APIClientError as exc:
            detail = str(exc).lower()
            if "user not found" not in detail:
                raise

            # Создаём пользователя, если есть данные Telegram-пользователя
            if username is None and full_name is None:
                raise

            await self.create_user(tg_id, username, full_name)
            return await _request()

    async def get_referral_info(self, tg_id: int):
        import httpx
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/api/referrals/{tg_id}/info")
            r.raise_for_status()
            return r.json()
    
    async def create_referral_payout(self, tg_id: int, referral_count: int):
        """Создать заявку на выплату рублей за рефералов"""
        url = f"{self.base_url}/api/referrals/{tg_id}/payout"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"referral_count": referral_count}) as resp:
                return await self._handle_response(resp)
    
    async def bind_referral(self, referred_tg: int, referrer_tg: int):
        url = f"{self.base_url}/api/referrals/bind"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params={
                "referred_tg": referred_tg,
                "referrer_tg": referrer_tg
            }) as resp:
                return await resp.json()
            
    async def query_ai(self, question: str, tg_id: int | None = None, gpt_model: str | None = None) -> str:
        """Запрос к AI с поддержкой выбора модели пользователя"""
        url = f"{self.base_url}/api/ai/query"
        payload = {"question": question}
        if tg_id:
            payload["tg_id"] = tg_id
        if gpt_model:
            payload["gpt_model"] = gpt_model
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                data = await self._handle_response(resp)
                return data.get("answer", "❌ Ошибка ответа от AI")
            
    async def get_user_file(self, tg_id: int):
        url = f"{self.base_url}/api/files/user/{tg_id}/get"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                text = await resp.text()
                if resp.status != 200:
                    raise Exception(f"Failed to get user file: {resp.status}, {text}")
                return await resp.json()

    async def regen_user_file(self, tg_id: int, filename: str | None = None):
        url = f"{self.base_url}/api/files/user/{tg_id}/regen"
        payload = {}
        if filename:
            payload["filename"] = filename
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload if payload else None) as resp:
                text = await resp.text()
                if resp.status not in (200, 201):
                    raise Exception(f"Failed to regen user file: {resp.status}, {text}")
                return await resp.json()

    async def get_admin_settings(self):
        url = f"{self.base_url}/api/admin/settings"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await self._handle_response(resp)
    
    async def get_user_generation_settings(self, tg_id: int):
        """Получить настройки генерации пользователя"""
        url = f"{self.base_url}/api/users/{tg_id}/generation-settings"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await self._handle_response(resp)
    
    async def update_user_generation_settings(self, tg_id: int, selected_model_key: str | None = None, selected_gpt_model: str | None = None, custom_prompt: str | None = None):
        """Обновить настройки генерации пользователя"""
        url = f"{self.base_url}/api/users/{tg_id}/generation-settings"
        payload = {}
        if selected_model_key is not None:
            payload["selected_model_key"] = selected_model_key
        if selected_gpt_model is not None:
            payload["selected_gpt_model"] = selected_gpt_model
        if custom_prompt is not None:
            payload["custom_prompt"] = custom_prompt
        
        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=payload) as resp:
                return await self._handle_response(resp)
    
    async def get_channel_settings(self):
        """Получить настройки канала"""
        url = f"{self.base_url}/api/admin/settings/channel"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await self._handle_response(resp)

    async def charge_tokens(self, tg_id: int, action: str):
        url = f"{self.base_url}/api/tokens/charge"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"tg_id": tg_id, "action": action}) as resp:
                return await self._handle_response(resp)

    async def get_token_pricing(self):
        url = f"{self.base_url}/api/tokens/pricing"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await self._handle_response(resp)
    
    async def get_image_models(self):
        """Получить список доступных моделей генерации изображений"""
        url = f"{self.base_url}/api/tokens/models"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await self._handle_response(resp)
    
    async def check_channel_subscription(self, tg_id: int):
        """Проверить подписку на канал и начислить бонус при необходимости"""
        url = f"{self.base_url}/api/channel/check-subscription/{tg_id}"
        async with aiohttp.ClientSession() as session:
            async with session.post(url) as resp:
                return await self._handle_response(resp)
    
    async def create_token_purchase_request(self, tg_id: int, amount: int, cost: float):
        """Создать заявку на пополнение токенов"""
        url = f"{self.base_url}/api/tokens/purchase"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={
                "tg_id": tg_id,
                "amount": amount,
                "cost": float(cost)
            }) as resp:
                return await self._handle_response(resp)
    
    async def get_topup_settings(self):
        """Получить настройки пополнения баланса"""
        url = f"{self.base_url}/api/tokens/topup-settings"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await self._handle_response(resp)
