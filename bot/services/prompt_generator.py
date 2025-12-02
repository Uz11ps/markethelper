import os
import json
import logging
from typing import List
from openai import AsyncOpenAI
from bot.services.api_client import APIClient

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=OPENAI_API_KEY)
settings_api = APIClient()


SYSTEM_PROMPT = """Ты — 'Деконструктор-Синтезатор Промтов' (Prompt Deconstructor & Synthesizer), ИИ-аналитик, специализирующийся на слиянии контента и стиля для генеративных моделей.

Твоя задача — получить на вход ДВА типа изображений:

1. [НОВЫЙ_ТОВАР.jpg] - Фото товара (может быть несколько)
2. [ДИЗАЙН_РЕФЕРЕНС.jpg] - Источник стиля (может быть несколько)

Ты должен выполнить "слияние" (merge):

1. **Идентифицировать главный объект** в фото товара (например, "a white ceramic mug", "a black running shoe", "a silver smartwatch")
2. **Деконструировать референс** на атомы стиля:
   - Тема/Формат: marketplace infographic card, studio shot, advertisement
   - Стиль: minimalist, eco-natural, premium-luxe, tech, photorealistic
   - Композиция: centered product, asymmetrical layout, text placement
   - Фон: solid white background #FFFFFF, gradient, studio background
   - Палитра: цветовая схема (hex коды)
   - Свет: soft studio lighting, dramatic side light, bright and airy
   - Элементы: icons, typography, graphics

3. **Сгенерировать промт** который объединяет стиль референса с товаром

**КРИТИЧЕСКИ ВАЖНО - ПРОФЕССИОНАЛЬНАЯ ФОТОСЪЁМКА:**
- Результат должен выглядеть как РЕАЛЬНАЯ ФОТОГРАФИЯ, снятая профессиональным фотографом
- ОБЯЗАТЕЛЬНО добавляй технические детали камеры: "shot on professional DSLR camera, Canon EOS R5, 50mm lens, f/2.8 aperture, natural lighting"
- Используй термины: "photorealistic", "hyperrealistic", "studio photography", "commercial product photography"
- Указывай детали освещения: "professional studio lighting setup, softbox lighting, three-point lighting"
- НЕ используй термины "illustration", "digital art", "CGI", "3D render"
- Акцент на реализм: "ultra sharp focus, high detail, natural textures, real photo"

**ВАЖНО:**
- Если на референсе есть текст, промт должен содержать: "...with text elements in Russian..."
- Промт должен быть на английском языке
- Опиши товар точно и детально

**ФОРМАТ ВЫВОДА - ТОЛЬКО JSON:**

{
  "generated_text_prompt": "Professional commercial product photography shot on Canon EOS R5, 50mm lens, f/2.8. Hyperrealistic marketplace infographic card featuring a centrally composed [описание товара] on a clean background. [детали стиля из референса]. Professional studio lighting setup with softbox, three-point lighting. Natural textures, ultra sharp focus, high detail. Color palette: [цвета]. Text elements in Russian. Icons and graphics as shown in reference. Real photo, not CGI, photorealistic quality. --style raw --ar 3:4",
  "deconstruction_analysis": {
    "product_identified": "Описание товара на русском",
    "style_source": "Стиль из референса",
    "layout_source": "Композиция из референса",
    "palette_source": "Цветовая палитра",
    "prompt_language": "Английский (для модели), с указанием 'text in Russian' если нужен текст"
  }
}

ВЫВОДИ ТОЛЬКО JSON БЕЗ ДОПОЛНИТЕЛЬНОГО ТЕКСТА!
"""


class PromptGeneratorService:
    """Сервис для генерации промптов через GPT-4o с vision"""

    _system_prompt_cache: str | None = None

    @classmethod
    async def _get_system_prompt(cls) -> str:
        if cls._system_prompt_cache:
            return cls._system_prompt_cache

        try:
            data = await settings_api.get_admin_settings()
            prompt = data.get("prompt_generator_prompt")
            if prompt:
                cls._system_prompt_cache = prompt
                return prompt
        except Exception as exc:
            logger.warning(f"Не удалось получить промпт генератора из админки: {exc}")

        cls._system_prompt_cache = SYSTEM_PROMPT
        return SYSTEM_PROMPT

    @classmethod
    async def generate_prompt_from_images(
        cls,
        product_image_urls: List[str],
        reference_image_urls: List[str]
    ) -> dict:
        """
        Генерация промпта на основе фото товара и референсов

        Args:
            product_image_urls: Список URL фотографий товара
            reference_image_urls: Список URL референсных изображений

        Returns:
            dict с полями:
                - generated_text_prompt: готовый промпт для генерации
                - deconstruction_analysis: анализ товара и стиля
        """
        try:
            logger.info(f"Генерация промпта из {len(product_image_urls)} фото товара и {len(reference_image_urls)} референсов")

            # Формируем контент для GPT-4o
            content = []

            # Добавляем текстовую инструкцию
            content.append({
                "type": "text",
                "text": "Проанализируй фотографии товара и референсы. Создай промпт для генерации карточки товара."
            })

            # Добавляем фото товара
            content.append({
                "type": "text",
                "text": f"\n\n**ФОТОГРАФИИ ТОВАРА ({len(product_image_urls)} шт.):**"
            })

            for i, url in enumerate(product_image_urls, 1):
                content.append({
                    "type": "image_url",
                    "image_url": {"url": url}
                })
                content.append({
                    "type": "text",
                    "text": f"Фото товара #{i}"
                })

            # Добавляем референсы
            content.append({
                "type": "text",
                "text": f"\n\n**ДИЗАЙН-РЕФЕРЕНСЫ ({len(reference_image_urls)} шт.):**"
            })

            for i, url in enumerate(reference_image_urls, 1):
                content.append({
                    "type": "image_url",
                    "image_url": {"url": url}
                })
                content.append({
                    "type": "text",
                    "text": f"Референс #{i}"
                })

            # Запрос к GPT-4o
            system_prompt = await cls._get_system_prompt()

            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1500,
                temperature=0.7,
            )

            # Парсим ответ
            answer = response.choices[0].message.content.strip()

            # Убираем возможные markdown блоки
            if answer.startswith("```json"):
                answer = answer[7:]
            if answer.startswith("```"):
                answer = answer[3:]
            if answer.endswith("```"):
                answer = answer[:-3]

            answer = answer.strip()

            # Парсим JSON
            result = json.loads(answer)

            logger.info(f"Промпт успешно сгенерирован: {result['generated_text_prompt'][:100]}...")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON от GPT: {e}\nОтвет: {answer}")
            raise ValueError(f"GPT вернул некорректный JSON: {e}")
        except Exception as e:
            logger.error(f"Ошибка при генерации промпта: {e}")
            raise

    @staticmethod
    async def analyze_product_only(product_image_urls: List[str]) -> str:
        """
        Анализ только товара без референса (для быстрого описания)

        Returns:
            Текстовое описание товара
        """
        try:
            content = [
                {
                    "type": "text",
                    "text": "Опиши этот товар кратко и точно на английском языке (например: 'a white wireless headphone', 'a black leather wallet')"
                }
            ]

            for url in product_image_urls:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": url}
                })

            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": content}
                ],
                max_tokens=100,
                temperature=0.3,
            )

            description = response.choices[0].message.content.strip()
            logger.info(f"Товар описан: {description}")

            return description

        except Exception as e:
            logger.error(f"Ошибка при анализе товара: {e}")
            raise
