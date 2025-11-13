import os
import asyncio
import logging
from typing import List
import fal_client

logger = logging.getLogger(__name__)

# Настраиваем FAL API ключ
FAL_API_KEY = os.getenv("FAL_API_KEY")
if FAL_API_KEY:
    os.environ["FAL_KEY"] = FAL_API_KEY
    logger.info("FAL API key loaded successfully")
else:
    logger.warning("FAL API key not found in environment variables")


class FALService:
    """Сервис для работы с FAL API и моделью Nano Banana"""

    @staticmethod
    async def generate_product_image(
        prompt: str,
        product_images: List[str],
        reference_images: List[str],
        num_images: int = 1,
        aspect_ratio: str = "3:4"
    ) -> List[str]:
        """
        Генерация изображения товара с применением стиля референсов

        Использует двухэтапный подход:
        1. Redux для применения стиля главного референса к товару
        2. Дополнительная генерация с учётом промпта

        Args:
            prompt: Текстовый промпт для генерации
            product_images: Список URL изображений товара
            reference_images: Список URL референсных изображений
            num_images: Количество изображений для генерации

        Returns:
            Список URL сгенерированных изображений
        """
        try:
            logger.info(f"Начало генерации с промптом: {prompt[:100]}...")

            # Основное изображение товара (первое из списка)
            main_product_image = product_images[0] if product_images else None

            if not main_product_image:
                raise ValueError("Необходимо хотя бы одно изображение товара")

            # Главный референс для стиля
            main_reference = reference_images[0] if reference_images else None

            if main_reference:
                # Используем Nano Banana для применения стиля референса к товару
                logger.info("Используется Nano Banana для применения стиля референса к товару")

                # Промпт инструкция для комбинирования
                combined_prompt = (
                    f"Apply the visual style, composition, lighting, background, and color palette "
                    f"from the reference image to the product image. "
                    f"{prompt}. Keep the product recognizable but apply the exact marketplace card style from reference."
                )

                # Nano Banana принимает image_urls - массив изображений (товар + референсы)
                image_urls_list = [main_product_image] + reference_images[:3]  # Товар + до 3 референсов

                arguments = {
                    "prompt": combined_prompt,
                    "image_urls": image_urls_list,  # Массив изображений для обработки
                    "num_images": num_images,
                    "aspect_ratio": aspect_ratio,
                    "output_format": "jpeg",
                }

                model = "fal-ai/nano-banana"
            else:
                # Без референса - обычная генерация
                logger.info("Генерация без референса - используется FLUX Pro Ultra")

                arguments = {
                    "prompt": prompt,
                    "num_images": num_images,
                    "image_size": "square_hd",
                    "num_inference_steps": 40,
                    "guidance_scale": 7.5,
                    "enable_safety_checker": True,
                }

                model = "fal-ai/flux-pro/v1.1-ultra"

            logger.info(f"Используется модель: {model}")
            logger.info(f"Параметры: {arguments}")

            # Асинхронный вызов FAL API
            result = await asyncio.to_thread(
                fal_client.subscribe,
                model,
                arguments=arguments,
                with_logs=True
            )

            # Извлекаем URL сгенерированных изображений
            if result and "images" in result:
                image_urls = [img["url"] for img in result["images"]]
                logger.info(f"Успешно сгенерировано {len(image_urls)} изображений")
                return image_urls
            else:
                logger.error("Не удалось получить изображения из ответа FAL API")
                return []

        except Exception as e:
            logger.error(f"Ошибка при генерации изображения: {e}")
            raise

    @staticmethod
    async def upload_image_to_fal(image_path: str) -> str:
        """
        Загрузка локального изображения в FAL storage

        Args:
            image_path: Путь к локальному файлу

        Returns:
            URL загруженного изображения
        """
        try:
            # Читаем файл как bytes
            with open(image_path, "rb") as f:
                file_bytes = f.read()

            # Загружаем bytes в FAL
            url = await asyncio.to_thread(
                fal_client.upload,
                file_bytes,
                "image/jpeg"
            )
            logger.info(f"Изображение загружено: {url}")
            return url
        except Exception as e:
            logger.error(f"Ошибка при загрузке изображения в FAL: {e}")
            raise
