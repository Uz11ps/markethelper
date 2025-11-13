import aiohttp
from bot.config import BACKEND_URL


class APIClient:
    def __init__(self):
        self.base_url = BACKEND_URL

    async def create_user(self, tg_id: int, username: str | None, full_name: str | None):
        url = f"{self.base_url}/admin/users/"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={
                "tg_id": tg_id,
                "username": username,
                "full_name": full_name,
            }) as resp:
                return await resp.json()

    async def get_user(self, tg_id: int):
        url = f"{self.base_url}/admin/users/by_tg/{tg_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.json()

    async def create_request(self, tg_id: int, tariff_code: str, duration_months: int):
        url = f"{self.base_url}/admin/requests/"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={
                "tg_id": tg_id,
                "tariff_code": tariff_code,
                "duration_months": duration_months
            }) as resp:
                return await resp.json()

    async def get_profile(self, tg_id: int):
        url = f"{self.base_url}/profile/{tg_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.json()

    async def get_referral_info(self, tg_id: int):
        import httpx
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/referrals/{tg_id}/info")
            r.raise_for_status()
            return r.json()
    
    async def bind_referral(self, referred_tg: int, referrer_tg: int):
        url = f"{self.base_url}/referrals/bind"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params={
                "referred_tg": referred_tg,
                "referrer_tg": referrer_tg
            }) as resp:
                return await resp.json()
            
    async def query_ai(self, question: str) -> str:
        url = f"{self.base_url}/ai/query"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"question": question}) as resp:
                data = await resp.json()
                return data.get("answer", "❌ Ошибка ответа от AI")
            
    async def get_user_file(self, tg_id: int):
        url = f"{self.base_url}/files/user/{tg_id}/get"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                text = await resp.text()
                if resp.status != 200:
                    raise Exception(f"Failed to get user file: {resp.status}, {text}")
                return await resp.json()

    async def regen_user_file(self, tg_id: int, filename: str | None = None):
        url = f"{self.base_url}/files/user/{tg_id}/regen"
        payload = {}
        if filename:
            payload["filename"] = filename
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload if payload else None) as resp:
                text = await resp.text()
                if resp.status not in (200, 201):
                    raise Exception(f"Failed to regen user file: {resp.status}, {text}")
                return await resp.json()