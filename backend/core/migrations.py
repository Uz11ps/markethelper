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


async def migrate_tariff_name():
    """Обновить название тарифа 'Групповой' на 'Складчина'"""
    try:
        from backend.models import Tariff
        conn = connections.get("default")
        
        # Обновляем название тарифа GROUP с "Групповой" на "Складчина"
        try:
            result = await conn.execute_query(
                "UPDATE tariffs SET name = 'Складчина' WHERE code = 'GROUP' AND name = 'Групповой'"
            )
            if result and hasattr(result, 'rowcount') and result.rowcount > 0:
                logger.info(f"✅ Обновлено {result.rowcount} записей тарифа GROUP: 'Групповой' -> 'Складчина'")
            else:
                # Проверяем, существует ли тариф с нужным названием
                tariff = await Tariff.get_or_none(code="GROUP")
                if tariff:
                    if tariff.name == "Складчина":
                        logger.debug("Тариф GROUP уже имеет название 'Складчина'")
                    else:
                        tariff.name = "Складчина"
                        await tariff.save()
                        logger.info("✅ Название тарифа GROUP обновлено на 'Складчина'")
                else:
                    logger.debug("Тариф GROUP не найден, будет создан при инициализации")
        except OperationalError as e:
            if "no such table" in str(e).lower():
                logger.debug(f"Таблица tariffs еще не создана: {e}")
            else:
                logger.error(f"Ошибка при обновлении названия тарифа: {e}")
                import traceback
                traceback.print_exc()
    except Exception as e:
        logger.error(f"Ошибка при миграции названия тарифа: {e}")
        import traceback
        traceback.print_exc()
        # Не прерываем запуск приложения, если миграция не удалась


async def migrate_users_table():
    """Добавить недостающие колонки в таблицу users если их нет"""
    try:
        conn = connections.get("default")
        
        # Проверяем существование колонок через PRAGMA table_info
        try:
            result = await conn.execute_query("PRAGMA table_info(users)")
            
            columns = []
            if result:
                for row in result:
                    if isinstance(row, (list, tuple)) and len(row) > 1:
                        columns.append(row[1])  # name - второй элемент
                    elif isinstance(row, dict):
                        columns.append(row.get('name', ''))
            
            # Список колонок, которые нужно добавить
            columns_to_add = [
                ("email", "VARCHAR(255) NULL", "Email для индивидуальных подписок"),
                ("channel_bonus_given", "BOOLEAN DEFAULT 0", "Был ли начислен бонус за подписку на канал"),
            ]
            
            for column_name, column_type, description in columns_to_add:
                if column_name not in columns:
                    logger.info(f"Добавляем колонку {column_name} в таблицу users ({description})")
                    try:
                        await conn.execute_query(
                            f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"
                        )
                        logger.info(f"✅ Колонка {column_name} успешно добавлена в таблицу users")
                    except OperationalError as alter_error:
                        if "duplicate column" in str(alter_error).lower():
                            logger.info(f"Колонка {column_name} уже существует")
                        else:
                            logger.error(f"Ошибка при добавлении колонки {column_name}: {alter_error}")
                            raise
                else:
                    logger.debug(f"Колонка {column_name} уже существует в таблице users")
        except OperationalError as e:
            # Если таблица не существует, это нормально - она будет создана автоматически
            if "no such table" in str(e).lower():
                logger.debug(f"Таблица users еще не создана: {e}")
            elif "duplicate column" in str(e).lower():
                logger.info("Колонки уже существуют (обнаружено через ошибку)")
            else:
                raise
    except OperationalError as e:
        if "duplicate column" in str(e).lower():
            logger.info("Колонки уже существуют (обнаружено через ошибку)")
        else:
            logger.error(f"Ошибка при миграции users_table: {e}")
            import traceback
            traceback.print_exc()
    except Exception as e:
        logger.error(f"Ошибка при миграции users_table: {e}")
        import traceback
        traceback.print_exc()
        # Не прерываем запуск приложения, если миграция не удалась

