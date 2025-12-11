"""
Миграции базы данных
"""
import logging
from tortoise import connections
from tortoise.exceptions import OperationalError

logger = logging.getLogger(__name__)


async def migrate_user_generation_settings():
    """Добавить колонку selected_gpt_model в таблицу user_generation_settings если её нет"""
    try:
        conn = connections.get("default")
        
        # Проверяем существование колонки через PRAGMA table_info
        # В SQLite PRAGMA table_info возвращает: (cid, name, type, notnull, dflt_value, pk)
        try:
            result = await conn.execute_query("PRAGMA table_info(user_generation_settings)")
            
            columns = []
            if result:
                for row in result:
                    if isinstance(row, (list, tuple)) and len(row) > 1:
                        columns.append(row[1])  # name - второй элемент
                    elif isinstance(row, dict):
                        columns.append(row.get('name', ''))
            
            if "selected_gpt_model" not in columns:
                logger.info("Добавляем колонку selected_gpt_model в таблицу user_generation_settings")
                try:
                    await conn.execute_query(
                        "ALTER TABLE user_generation_settings ADD COLUMN selected_gpt_model VARCHAR(255) NULL"
                    )
                    logger.info("✅ Колонка selected_gpt_model успешно добавлена")
                except OperationalError as alter_error:
                    # Если колонка уже существует (возможно была добавлена между проверкой и добавлением)
                    if "duplicate column" in str(alter_error).lower():
                        logger.info("Колонка selected_gpt_model уже существует (обнаружено при добавлении)")
                    else:
                        raise
            else:
                logger.debug("Колонка selected_gpt_model уже существует")
        except OperationalError as e:
            # Если таблица не существует, это нормально - она будет создана автоматически
            if "no such table" in str(e).lower():
                logger.debug(f"Таблица user_generation_settings еще не создана: {e}")
            elif "duplicate column" in str(e).lower():
                logger.info("Колонка selected_gpt_model уже существует (обнаружено через ошибку)")
            else:
                raise
    except OperationalError as e:
        # Если колонка уже существует (duplicate column), это нормально
        if "duplicate column" in str(e).lower():
            logger.info("Колонка selected_gpt_model уже существует (обнаружено через ошибку)")
        else:
            logger.error(f"Ошибка при миграции user_generation_settings: {e}")
            import traceback
            traceback.print_exc()
    except Exception as e:
        logger.error(f"Ошибка при миграции user_generation_settings: {e}")
        import traceback
        traceback.print_exc()
        # Не прерываем запуск приложения, если миграция не удалась


async def migrate_requests_table():
    """Добавить колонки subscription_type, group_id, user_email в таблицу requests если их нет"""
    try:
        conn = connections.get("default")
        
        # Проверяем существование колонок через PRAGMA table_info
        try:
            result = await conn.execute_query("PRAGMA table_info(requests)")
            
            columns = []
            if result:
                for row in result:
                    if isinstance(row, (list, tuple)) and len(row) > 1:
                        columns.append(row[1])  # name - второй элемент
                    elif isinstance(row, dict):
                        columns.append(row.get('name', ''))
            
            # Добавляем subscription_type если его нет
            if "subscription_type" not in columns:
                logger.info("Добавляем колонку subscription_type в таблицу requests")
                try:
                    await conn.execute_query(
                        "ALTER TABLE requests ADD COLUMN subscription_type VARCHAR(20) DEFAULT 'group'"
                    )
                    logger.info("✅ Колонка subscription_type успешно добавлена")
                except OperationalError as alter_error:
                    if "duplicate column" in str(alter_error).lower():
                        logger.info("Колонка subscription_type уже существует")
                    else:
                        raise
            
            # Добавляем group_id если его нет
            if "group_id" not in columns:
                logger.info("Добавляем колонку group_id в таблицу requests")
                try:
                    await conn.execute_query(
                        "ALTER TABLE requests ADD COLUMN group_id INTEGER NULL"
                    )
                    logger.info("✅ Колонка group_id успешно добавлена")
                except OperationalError as alter_error:
                    if "duplicate column" in str(alter_error).lower():
                        logger.info("Колонка group_id уже существует")
                    else:
                        raise
            
            # Добавляем user_email если его нет
            if "user_email" not in columns:
                logger.info("Добавляем колонку user_email в таблицу requests")
                try:
                    await conn.execute_query(
                        "ALTER TABLE requests ADD COLUMN user_email VARCHAR(255) NULL"
                    )
                    logger.info("✅ Колонка user_email успешно добавлена")
                except OperationalError as alter_error:
                    if "duplicate column" in str(alter_error).lower():
                        logger.info("Колонка user_email уже существует")
                    else:
                        raise
        except OperationalError as e:
            # Если таблица не существует, это нормально - она будет создана автоматически
            if "no such table" in str(e).lower():
                logger.debug(f"Таблица requests еще не создана: {e}")
            elif "duplicate column" in str(e).lower():
                logger.info("Колонки уже существуют (обнаружено через ошибку)")
            else:
                raise
    except OperationalError as e:
        if "duplicate column" in str(e).lower():
            logger.info("Колонки уже существуют (обнаружено через ошибку)")
        else:
            logger.error(f"Ошибка при миграции requests: {e}")
            import traceback
            traceback.print_exc()
    except Exception as e:
        logger.error(f"Ошибка при миграции requests: {e}")
        import traceback
        traceback.print_exc()
        # Не прерываем запуск приложения, если миграция не удалась

