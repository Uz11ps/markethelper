"""
Миграции базы данных
"""
import logging
from tortoise import connections

logger = logging.getLogger(__name__)


async def migrate_user_generation_settings():
    """Добавить колонку selected_gpt_model в таблицу user_generation_settings если её нет"""
    try:
        conn = connections.get("default")
        
        # Проверяем существование колонки через PRAGMA table_info
        result = await conn.execute_query(
            "PRAGMA table_info(user_generation_settings)"
        )
        
        # result может быть списком кортежей или списком строк
        # В SQLite PRAGMA table_info возвращает: (cid, name, type, notnull, dflt_value, pk)
        columns = []
        if result:
            for row in result:
                if isinstance(row, (list, tuple)) and len(row) > 1:
                    columns.append(row[1])  # name - второй элемент
                elif isinstance(row, dict):
                    columns.append(row.get('name', ''))
        
        if "selected_gpt_model" not in columns:
            logger.info("Добавляем колонку selected_gpt_model в таблицу user_generation_settings")
            await conn.execute_query(
                "ALTER TABLE user_generation_settings ADD COLUMN selected_gpt_model VARCHAR(255) NULL"
            )
            logger.info("✅ Колонка selected_gpt_model успешно добавлена")
        else:
            logger.debug("Колонка selected_gpt_model уже существует")
    except Exception as e:
        logger.error(f"Ошибка при миграции user_generation_settings: {e}")
        import traceback
        traceback.print_exc()
        # Не прерываем запуск приложения, если миграция не удалась
        # Пользователь может выполнить её вручную

