#!/usr/bin/env python3
"""
Простой скрипт для очистки базы данных (работает внутри контейнера)
"""
import asyncio
import sys

# Добавляем путь к проекту
sys.path.insert(0, '/app')

from tortoise import Tortoise
from backend.core.db import TORTOISE_ORM
# Импорты моделей не нужны, используем прямой SQL


async def clear_database(keep_admin_id=None):
    """Очистка базы данных с сохранением настроек"""
    
    await Tortoise.init(config=TORTOISE_ORM)
    
    print("=" * 60)
    print("ОЧИСТКА БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    if keep_admin_id:
        print(f"Сохраняем админа с ID={keep_admin_id}")
    else:
        print("Удаляем ВСЕХ админов!")
    
    print("\nУдаление данных...")
    
    # Используем прямой SQL для удаления данных
    conn = Tortoise.get_connection("default")
    
    # Список таблиц для очистки (в правильном порядке из-за внешних ключей)
    tables_to_clear = [
        "channel_bonus_requests",
        "user_generation_settings",
        "pending_bonuses",
        "referral_payouts",
        "referrals",
        "token_purchase_requests",
        "requests",
        "subscriptions",
        "ai_requests",
        "product_descriptions",
        "editable_prompt_templates",
        "infographic_projects",
        "mailings",
        "broadcast_messages",
        "users",
        "access_groups",
        "access_files",
        "design_templates"
    ]
    
    for table in tables_to_clear:
        try:
            result = await conn.execute_query(f"SELECT COUNT(*) FROM {table}")
            count = result[1][0][0] if result[1] else 0
            if count > 0:
                await conn.execute_query(f"DELETE FROM {table}")
                print(f"✓ Удалено из {table}: {count}")
        except Exception as e:
            print(f"⚠ Ошибка при удалении из {table}: {e}")
    
    # Удаляем админов (кроме указанного ID)
    if keep_admin_id:
        try:
            result = await conn.execute_query(f"SELECT COUNT(*) FROM admins WHERE id != {keep_admin_id}")
            count = result[1][0][0] if result[1] else 0
            if count > 0:
                await conn.execute_query(f"DELETE FROM admins WHERE id != {keep_admin_id}")
                admin_result = await conn.execute_query(f"SELECT username FROM admins WHERE id = {keep_admin_id}")
                admin_name = admin_result[1][0][0] if admin_result[1] and admin_result[1][0] else "неизвестно"
                print(f"✓ Удалено админов: {count} (сохранен ID={keep_admin_id}: {admin_name})")
        except Exception as e:
            print(f"⚠ Ошибка при удалении админов: {e}")
    else:
        try:
            result = await conn.execute_query("SELECT COUNT(*) FROM admins")
            count = result[1][0][0] if result[1] else 0
            if count > 0:
                await conn.execute_query("DELETE FROM admins")
                print(f"✓ Удалено админов: {count}")
        except Exception as e:
            print(f"⚠ Ошибка при удалении админов: {e}")
    
    print("\n✅ ГОТОВО! Настройки сохранены.")
    
    await Tortoise.close_connections()


if __name__ == "__main__":
    keep_admin = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(clear_database(keep_admin))

