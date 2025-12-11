import os
import json
import re
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
    async def _get_system_prompt(cls, force_refresh: bool = False) -> str:
        """Получить системный промпт из админки или использовать дефолтный"""
        if cls._system_prompt_cache and not force_refresh:
            return cls._system_prompt_cache

        try:
            data = await settings_api.get_admin_settings()
            prompt = data.get("prompt_generator_prompt")
            if prompt and prompt.strip():
                logger.info(f"Используется промпт из админки (длина: {len(prompt)} символов)")
                cls._system_prompt_cache = prompt
                return prompt
            else:
                logger.warning("Промпт из админки пустой или отсутствует, используется дефолтный")
        except Exception as exc:
            logger.warning(f"Не удалось получить промпт генератора из админки: {exc}")

        cls._system_prompt_cache = SYSTEM_PROMPT
        return SYSTEM_PROMPT
    
    @classmethod
    def clear_cache(cls):
        """Очистить кэш промпта для принудительного обновления"""
        cls._system_prompt_cache = None
        logger.info("Кэш промпта очищен")

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
            system_prompt = await cls._get_system_prompt(force_refresh=False)
            logger.info(f"Используется системный промпт (длина: {len(system_prompt)} символов, первые 200 символов: {system_prompt[:200]}...)")

            logger.info("Отправка запроса к GPT-4o для генерации промпта...")
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1500,
                temperature=0.7,
                response_format={"type": "json_object"}  # Принудительно запрашиваем JSON
            )

            # Проверяем наличие ответа
            if not response.choices or len(response.choices) == 0:
                logger.error("GPT вернул пустой список choices")
                raise ValueError("GPT вернул пустой ответ. Попробуйте ещё раз позже.")
            
            # Парсим ответ
            raw_content = response.choices[0].message.content
            if raw_content is None:
                logger.error("GPT вернул None в content")
                raise ValueError("GPT вернул пустой ответ. Попробуйте ещё раз позже.")
            
            answer = raw_content.strip()
            logger.info(f"Получен ответ от GPT (длина: {len(answer)}): {answer[:200]}...")

            # Проверяем, что ответ не пустой
            if not answer:
                logger.error("GPT вернул пустой ответ после strip()")
                raise ValueError("GPT вернул пустой ответ. Попробуйте ещё раз позже.")

            # Убираем возможные markdown блоки
            original_answer = answer
            if answer.startswith("```json"):
                answer = answer[7:]
                logger.debug("Удален префикс ```json")
            elif answer.startswith("```"):
                answer = answer[3:]
                logger.debug("Удален префикс ```")
            if answer.endswith("```"):
                answer = answer[:-3]
                logger.debug("Удален суффикс ```")

            answer = answer.strip()
            logger.debug(f"После удаления markdown (длина: {len(answer)}): {answer[:200]}...")

            # Пытаемся найти JSON в ответе, если он обернут в текст
            json_start = answer.find("{")
            json_end = answer.rfind("}") + 1
            
            if json_start == -1:
                logger.warning(f"Не найден символ '{{' в ответе. Ответ: {answer[:500]}")
                # Пытаемся найти JSON с помощью regex
                json_match = re.search(r'\{.*\}', answer, re.DOTALL)
                if json_match:
                    answer = json_match.group(0)
                    logger.info("JSON найден с помощью regex")
                else:
                    raise ValueError(f"Не найден JSON в ответе GPT. Ответ: {answer[:300]}...")
            elif json_end <= json_start:
                logger.warning(f"Некорректные индексы JSON: start={json_start}, end={json_end}")
                # Пытаемся найти JSON с помощью regex
                json_match = re.search(r'\{.*\}', answer, re.DOTALL)
                if json_match:
                    answer = json_match.group(0)
                    logger.info("JSON найден с помощью regex после некорректных индексов")
                else:
                    raise ValueError(f"Не найден валидный JSON в ответе GPT. Ответ: {answer[:300]}...")
            else:
                answer = answer[json_start:json_end]
                logger.debug(f"Извлечен JSON (длина: {len(answer)}): {answer[:200]}...")

            # Проверяем, что после извлечения JSON не пустой
            if not answer or not answer.strip():
                logger.error(f"После извлечения JSON получилась пустая строка. Оригинальный ответ: {original_answer[:500]}")
                raise ValueError("Не удалось извлечь JSON из ответа GPT. Попробуйте ещё раз позже.")

            # Парсим JSON
            try:
                result = json.loads(answer)
                logger.info("JSON успешно распарсен")
            except json.JSONDecodeError as json_err:
                logger.error(f"Ошибка парсинга JSON от GPT: {json_err}\nОтвет GPT: {answer[:500]}\nОригинальный ответ: {original_answer[:500]}")
                # Пытаемся извлечь JSON из текста с помощью регулярных выражений (более агрессивный поиск)
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', original_answer, re.DOTALL)
                if json_match:
                    try:
                        extracted_json = json_match.group(0)
                        logger.info(f"Попытка парсинга извлеченного JSON: {extracted_json[:200]}...")
                        result = json.loads(extracted_json)
                        logger.info("JSON успешно извлечен с помощью regex")
                    except json.JSONDecodeError as regex_err:
                        logger.error(f"Не удалось распарсить JSON даже после regex: {regex_err}")
                        raise ValueError(f"GPT вернул некорректный JSON. Ответ: {answer[:200]}...")
                else:
                    raise ValueError(f"GPT вернул некорректный JSON: {json_err}. Ответ: {answer[:200]}...")

            # Проверяем наличие обязательных полей
            if not isinstance(result, dict):
                logger.error(f"Результат парсинга не является словарем: {type(result)}, значение: {result}")
                raise ValueError("GPT вернул ответ в неверном формате. Ожидался JSON объект.")
            
            if "generated_text_prompt" not in result:
                logger.error(f"В ответе GPT отсутствует поле 'generated_text_prompt'. Доступные поля: {list(result.keys())}. Ответ: {answer[:500]}")
                # Попытка создать дефолтный промпт из того, что есть
                if original_answer and len(original_answer) > 50:
                    logger.warning("Попытка использовать оригинальный ответ как промпт")
                    result = {
                        "generated_text_prompt": original_answer[:500],
                        "deconstruction_analysis": {
                            "product_identified": "Не удалось определить",
                            "style_source": "Не удалось определить",
                            "layout_source": "Не удалось определить",
                            "palette_source": "Не удалось определить"
                        }
                    }
                    logger.info("Создан fallback промпт из оригинального ответа")
                else:
                    raise ValueError("GPT вернул ответ без обязательного поля 'generated_text_prompt'")

            logger.info(f"Промпт успешно сгенерирован: {result['generated_text_prompt'][:100]}...")

            return result

        except json.JSONDecodeError as e:
            error_msg = f"Ошибка парсинга JSON: {e}"
            if 'answer' in locals():
                error_msg += f"\nОтвет GPT: {answer[:500] if answer else 'Пустой ответ'}"
            if 'original_answer' in locals():
                error_msg += f"\nОригинальный ответ: {original_answer[:500] if original_answer else 'Нет оригинала'}"
            logger.error(error_msg)
            raise ValueError(f"GPT вернул некорректный JSON: {e}")
        except ValueError as e:
            # Пробрасываем ValueError как есть (уже обработанные ошибки)
            logger.error(f"ValueError при генерации промпта: {e}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при генерации промпта: {e}", exc_info=True)
            raise ValueError(f"Ошибка при генерации промпта: {str(e)}")

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
