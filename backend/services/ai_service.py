import os
import asyncio
import logging
import uuid
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import AsyncOpenAI
import pdfplumber
from dotenv import load_dotenv
from backend.services.settings_service import SettingsService

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_service")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    client_openai = AsyncOpenAI(api_key=OPENAI_API_KEY)
else:
    client_openai = None
    logger.warning("OPENAI_API_KEY is not set. AI features will be unavailable.")

os.environ["OMP_NUM_THREADS"] = "2"

semaphore = asyncio.Semaphore(1)
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name="knowledge",
    embedding_function=embedding_functions.DefaultEmbeddingFunction()
)

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)


async def add_text(text: str, metadata: dict):
    logger.info("Начало добавления текста в ChromaDB")

    try:
        doc_id = str(uuid.uuid4())  # генерируем уникальный ID
        await asyncio.to_thread(
            lambda: collection.add(
                ids=[doc_id],
                documents=[text],
                metadatas=[metadata],
            )
        )
        logger.info(f"Текст добавлен: {doc_id[:8]}...")

    except Exception as e:
        logger.error(f"Ошибка при добавлении текста: {e}")
        raise

async def list_texts():
    """
    Возвращает список объектов: { id, text, metadata }
    """
    logger.info("Запрос списка всех текстов")
    try:
        result = await asyncio.to_thread(lambda: collection.get())
        ids = result.get("ids", []) or []
        docs = result.get("documents", []) or []
        metas = result.get("metadatas", []) or []

        texts = []
        max_len = max(len(ids), len(docs), len(metas))
        for i in range(max_len):
            _id = ids[i] if i < len(ids) else None
            doc = docs[i] if i < len(docs) else ""
            meta = metas[i] if i < len(metas) else {}
            texts.append({"id": _id, "text": doc, "metadata": meta})
        logger.info(f"Найдено {len(texts)} текстов")
        return texts
    except Exception as e:
        logger.error(f"Ошибка при получении текстов: {e}")
        return []

async def query_ai(question: str, tg_id: int = None, gpt_model: str = None) -> str:
    logger.info(f"Запрос AI: {question}, tg_id: {tg_id}, gpt_model: {gpt_model}")

    context = ""
    try:
        results = await asyncio.to_thread(
            lambda: collection.query(query_texts=[question], n_results=3)
        )
        if results and results["documents"]:
            context = "\n".join(results["documents"][0])
            logger.info(f"Найден контекст: {context[:100]}...")
    except Exception as e:
        logger.error(f"Ошибка при поиске контекста: {e}")

    # Получаем кастомный промпт из настроек
    system_prompt = await SettingsService.get_ai_prompt()
    logger.info(f"[query_ai] Используется системный промпт из админки (длина: {len(system_prompt)} символов, первые 200 символов: {system_prompt[:200]}...)")

    # Формируем user сообщение с вопросом и контекстом
    user_content = f"""Вопрос пользователя:
{question}

Контекст (фрагменты из базы знаний):
{context}

Используй контекст для формирования точного и полезного ответа. Если контекста недостаточно, честно скажи об этом.
"""
    
    if not client_openai:
        logger.error("OpenAI client not initialized. Check OPENAI_API_KEY.")
        return "❌ Сервис ИИ недоступен. Проверьте настройки."
    
    # Определяем модель для использования
    # Приоритет: переданный gpt_model > модель пользователя > системная модель
    model_to_use = "gpt-4o-mini"  # По умолчанию
    
    if gpt_model:
        # Если модель передана явно, используем её
        model_to_use = gpt_model
        logger.info(f"Используется переданная модель: {model_to_use}")
    elif tg_id:
        # Пытаемся получить модель пользователя
        try:
            from backend.models.user import User
            from backend.models.user_generation_settings import UserGenerationSettings
            user = await User.get_or_none(tg_id=tg_id)
            if user:
                settings = await UserGenerationSettings.get_or_none(user=user)
                if settings and settings.selected_gpt_model:
                    model_to_use = settings.selected_gpt_model
                    logger.info(f"Используется модель пользователя: {model_to_use}")
        except Exception as e:
            logger.warning(f"Не удалось получить модель пользователя: {e}")
    
    # Если модель всё ещё дефолтная, используем системную
    if model_to_use == "gpt-4o-mini":
        try:
            model_to_use = await SettingsService.get_gpt_model()
            logger.info(f"Используется системная модель GPT: {model_to_use}")
        except Exception as e:
            logger.warning(f"Не удалось получить системную модель GPT: {e}")
    
    try:
        # Увеличенный таймаут для OpenAI запросов
        # Используем системный промпт правильно через role="system"
        response = await asyncio.wait_for(
            client_openai.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.7,
            ),
            timeout=240.0  # 4 минуты таймаут
        )
        answer = response.choices[0].message.content
        logger.info(f"Ответ от OpenAI получен (модель: {model_to_use})")
        return answer
    except Exception as e:
        logger.error(f"Ошибка при запросе к OpenAI: {e}")
        return "❌ Ошибка при обработке запроса AI"

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200):
    """
    Разбиваем длинный текст на чанки для векторной БД.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start += chunk_size - overlap
    return [c for c in chunks if c]

async def delete_text(text_id: str) -> bool:
    logger.info(f"Попытка удаления текста: {text_id}")
    try:
        await asyncio.to_thread(lambda: collection.delete(ids=[text_id]))
        logger.info(f"Удаление успешно: {text_id}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении текста {text_id}: {e}")
        return False

