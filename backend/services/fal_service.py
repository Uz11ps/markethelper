import asyncio
import logging
import os
from typing import Any, Dict, Optional, Sequence

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("fal_service")


class FalAIError(RuntimeError):
    """Исключение при ошибках обращения к FAL AI."""


class FalAIClient:
    """
    Клиент для работы с FAL AI моделями генерации и апскейла изображений.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("FAL_API_KEY")
        self.base_url = os.getenv("FAL_API_BASE_URL", "https://fal.run")
        self.default_image_model = os.getenv(
            "FAL_IMAGE_MODEL", 
            "fal-ai/flux-pro/v1.1",
        )
        self.default_upscale_model = os.getenv("FAL_UPSCALE_MODEL")
        self.poll_interval = float(os.getenv("FAL_POLL_INTERVAL", "2.0"))
        self.max_wait_seconds = float(os.getenv("FAL_MAX_WAIT_SECONDS", "120"))
        self.max_retries = int(os.getenv("FAL_MAX_RETRIES", "3"))
        self.retry_backoff = float(os.getenv("FAL_RETRY_BACKOFF", "1.5"))
        self.default_image_prompt_strength = float(os.getenv("FAL_IMAGE_PROMPT_STRENGTH", "0.85"))

        if not self.api_key:
            logger.warning("FAL_API_KEY не установлен. Генерация изображений недоступна.")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json",
        }

    def _normalized_base_url(self) -> str:
        """
        Приводит базовый URL к рабочему эндпоинту API FAL.
        """
        base = (self.base_url or "").strip()
        if not base:
            return "https://fal.run"

        base = base.rstrip("/")
        # Старый формат из .env (https://fal.ai/models) перенаправляем на fal.run
        if "fal.ai" in base:
            return "https://fal.run"
        # Удаляем завершающий /api, если он был указан вручную
        if base.endswith("/api"):
            base = base[:-4]
        return base

    def _build_model_url(self, model: str) -> str:
        return f"{self._normalized_base_url()}/{model.strip('/')}"

    async def _poll_response(self, url: str) -> Dict[str, Any]:
        """
        Ожидает готовности результата по указанному response_url.
        """
        if not url.startswith("http"):
            raise FalAIError("Некорректный response_url")

        loop = asyncio.get_running_loop()
        deadline = loop.time() + self.max_wait_seconds
        async with httpx.AsyncClient(timeout=self.max_wait_seconds, http2=True) as client:
            while True:
                if loop.time() > deadline:
                    raise FalAIError("Таймаут ожидания ответа FAL AI")

                try:
                    response = await client.get(url, headers=self._headers())
                except httpx.HTTPError as exc:
                    logger.error("FAL AI polling failed: %s", exc)
                    raise FalAIError("Ошибка сети при получении ответа FAL AI") from exc
                if response.status_code >= 400:
                    logger.error("FAL AI error %s: %s", response.status_code, response.text)
                    raise FalAIError(
                        f"FAL AI error {response.status_code}: {response.text}",
                    )

                try:
                    data = response.json()
                except ValueError as exc:
                    logger.error("FAL AI вернул некорректный JSON: %s", response.text)
                    raise FalAIError("FAL AI вернул некорректный JSON") from exc

                status = str(data.get("status") or data.get("state") or "").upper()
                if status in {"PENDING", "IN_PROGRESS", "RUNNING"}:
                    await asyncio.sleep(self.poll_interval)
                    continue

                return data

    async def _invoke_model(self, model: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            raise FalAIError("FAL_API_KEY не задан")
        if not model:
            raise FalAIError("Не указан идентификатор модели FAL AI")

        url = self._build_model_url(model)
        headers = self._headers()
        response: Optional[httpx.Response] = None
        last_exc: Optional[Exception] = None

        for attempt in range(1, max(self.max_retries, 1) + 1):
            try:
                async with httpx.AsyncClient(timeout=self.max_wait_seconds, http2=True) as client:
                    response = await client.post(url, headers=headers, json=payload)
                break
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt >= self.max_retries:
                    logger.error("FAL AI request failed after %s attempts: %s", attempt, exc)
                    raise FalAIError("Сбой сети при обращении к FAL AI") from exc
                backoff = self.retry_backoff * attempt
                logger.warning(
                    "FAL AI request failed (attempt %s/%s): %s. Retrying in %.1f s",
                    attempt,
                    self.max_retries,
                    exc,
                    backoff,
                )
                await asyncio.sleep(backoff)

        if response is None:
            raise FalAIError("Не удалось выполнить запрос к FAL AI") from last_exc

        if response.status_code >= 400:
            logger.error("FAL AI error %s: %s", response.status_code, response.text)
            raise FalAIError(f"FAL AI error {response.status_code}: {response.text}")

        try:
            data = response.json()
        except ValueError as exc:
            logger.error("FAL AI вернул некорректный JSON: %s", response.text)
            raise FalAIError("FAL AI вернул некорректный JSON") from exc

        # Если ответ содержит ссылку на итоговый результат — дожидаемся его.
        response_url = data.get("response_url")
        if response_url:
            return await self._poll_response(response_url)

        return data

    async def generate_image(
        self,
        prompt: str,
        *,
        negative_prompt: Optional[str] = None,
        reference_image_url: Optional[str] = None,
        reference_image_base64: Optional[str] = None,
        reference_image_urls: Optional[Sequence[str]] = None,
        reference_images_base64: Optional[Sequence[str]] = None,
        product_image_count: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        seed: Optional[int] = None,
        model: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Запускает генерацию изображения через FAL AI.
        """
        logger.info("=== FAL AI GENERATION PROMPT ===")
        logger.info("Final prompt:\n%s", prompt)
        if negative_prompt:
            logger.info("Negative prompt: %s", negative_prompt)
        logger.info("Model: %s", model or self.default_image_model)
        logger.info("=== END PROMPT ===")
        
        payload: Dict[str, Any] = {"prompt": prompt}

        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        has_image_prompt = False
        if reference_image_url:
            payload["image_url"] = reference_image_url
            has_image_prompt = True
        if reference_image_base64:
            mime = self._guess_mime_type(reference_image_base64)
            payload["image_url"] = f"data:{mime};base64,{reference_image_base64}"
            has_image_prompt = True
        if reference_images_base64:
            payload["reference_images_base64"] = list(reference_images_base64)
        if reference_image_urls:
            payload["reference_image_urls"] = list(reference_image_urls)
        if product_image_count is not None:
            payload["product_image_count"] = product_image_count
        if has_image_prompt and "image_prompt_strength" not in payload:
            payload["image_prompt_strength"] = self.default_image_prompt_strength

        if width:
            payload["width"] = width
        if height:
            payload["height"] = height
        if steps:
            payload["steps"] = steps
        if guidance_scale:
            payload["guidance_scale"] = guidance_scale
        if seed is not None:
            payload["seed"] = seed
        if extra:
            payload.update({k: v for k, v in extra.items() if v is not None})

        model_name = model or self.default_image_model
        return await self._invoke_model(model_name, payload)

    async def upscale_image(
        self,
        image_url: str,
        *,
        model: Optional[str] = None,
        scale: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Запускает апскейл изображения через FAL AI.
        """
        model_name = model or self.default_upscale_model
        if not model_name:
            raise FalAIError("Не задана модель апскейла (FAL_UPSCALE_MODEL)")

        payload: Dict[str, Any] = {"image_url": image_url}
        if scale:
            payload["scale"] = scale
        if extra:
            payload.update({k: v for k, v in extra.items() if v is not None})

        return await self._invoke_model(model_name, payload)

    async def job_status(self, job_reference: str) -> Dict[str, Any]:
        """
        Получает статус задания по request_id или полному URL.
        """
        if not self.api_key:
            raise FalAIError("FAL_API_KEY не задан")

        if job_reference.startswith("http"):
            url = job_reference
        else:
            model = self.default_image_model or self.default_upscale_model
            if not model:
                raise FalAIError("Не удалось определить модель для статуса задания")
            url = f"{self._normalized_base_url()}/{model.strip('/')}/requests/{job_reference}"

        async with httpx.AsyncClient(timeout=self.max_wait_seconds, http2=True) as client:
            response = await client.get(url, headers=self._headers())

        if response.status_code >= 400:
            logger.error("FAL AI job error %s: %s", response.status_code, response.text)
            raise FalAIError(f"FAL AI job error {response.status_code}: {response.text}")

        try:
            return response.json()
        except ValueError as exc:
            logger.error("FAL AI вернул некорректный JSON: %s", response.text)
            raise FalAIError("FAL AI вернул некорректный JSON") from exc

    async def health_check(self) -> Dict[str, Any]:
        """
        Проверяет доступность FAL AI API (через HEAD запрос к модели).
        """
        if not self.api_key:
            raise FalAIError("FAL_API_KEY не задан")

        model = self.default_image_model
        if not model:
            raise FalAIError("Не задана модель для health-check")

        url = self._build_model_url(model)
        async with httpx.AsyncClient(timeout=10, http2=True) as client:
            response = await client.head(url, headers=self._headers())

        if response.status_code >= 400:
            logger.error("FAL AI health error %s: %s", response.status_code, response.text)
            raise FalAIError(f"FAL AI health error {response.status_code}: {response.text}")

        return {"status": "ok"}

    @staticmethod
    def _guess_mime_type(b64_data: str) -> str:
        if b64_data.startswith("iVBOR"):
            return "image/png"
        if b64_data.startswith("/9j/"):
            return "image/jpeg"
        if b64_data.startswith("R0lGOD"):
            return "image/gif"
        return "image/jpeg"


fal_client = FalAIClient()
