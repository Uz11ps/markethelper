#!/usr/bin/env python3
"""
Скрипт для очистки базы данных от пользователей, админов и групп
Настройки (settings) сохраняются
"""
import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from tortoise import Tortoise
from backend.models import (
    User, Admin, AccessGroup, Subscription, Request,
    ChannelBonusRequest, UserGenerationSettings, PendingBonus,
    ReferralPayout, Referral, TokenPurchaseRequest,
    AccessFile, AIRequest, ProductDescription, EditablePromptTemplate,
    InfographicProject, DesignTemplate, Mailing, BroadcastMessage
)

TORTOISE_ORM = {
    "connections": {
        "default": "sqlite:///app/data/db.sqlite3"
    },
    "apps": {
        "models": {
            "models": ["backend.models"],
            "default_connection": "default",
        }
    },
}


async def clear_database(keep_admin_id=None):
    """Очистка базы данных с сохранением настроек"""
    
    # Инициализация подключения
    await Tortoise.init(config=TORTOISE_ORM)
    
    print("=" * 60)
    print("НАЧИНАЕМ ОЧИСТКУ БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    if keep_admin_id:
        print(f"⚠️  Будет сохранен админ с ID={keep_admin_id}")
    else:
        print("⚠️  ВСЕ админы будут удалены!")
    
    print("\nУдаление связанных данных...")
    
    # Удаляем связанные данные пользователей
    count = await ChannelBonusRequest.all().count()
    await ChannelBonusRequest.all().delete()
    print(f"  ✓ Удалено запросов на бонус за канал: {count}")
    
    count = await UserGenerationSettings.all().count()
    await UserGenerationSettings.all().delete()
    print(f"  ✓ Удалено настроек генерации: {count}")
    
    count = await PendingBonus.all().count()
    await PendingBonus.all().delete()
    print(f"  ✓ Удалено ожидающих бонусов: {count}")
    
    count = await ReferralPayout.all().count()
    await ReferralPayout.all().delete()
    print(f"  ✓ Удалено выплат рефералов: {count}")
    
    count = await Referral.all().count()
    await Referral.all().delete()
    print(f"  ✓ Удалено рефералов: {count}")
    
    count = await TokenPurchaseRequest.all().count()
    await TokenPurchaseRequest.all().delete()
    print(f"  ✓ Удалено заявок на покупку токенов: {count}")
    
    count = await Request.all().count()
    await Request.all().delete()
    print(f"  ✓ Удалено заявок: {count}")
    
    count = await Subscription.all().count()
    await Subscription.all().delete()
    print(f"  ✓ Удалено подписок: {count}")
    
    count = await AIRequest.all().count()
    await AIRequest.all().delete()
    print(f"  ✓ Удалено запросов к AI: {count}")
    
    count = await ProductDescription.all().count()
    await ProductDescription.all().delete()
    print(f"  ✓ Удалено описаний товаров: {count}")
    
    count = await EditablePromptTemplate.all().count()
    await EditablePromptTemplate.all().delete()
    print(f"  ✓ Удалено шаблонов промптов: {count}")
    
    count = await InfographicProject.all().count()
    await InfographicProject.all().delete()
    print(f"  ✓ Удалено проектов инфографики: {count}")
    
    count = await Mailing.all().count()
    await Mailing.all().delete()
    print(f"  ✓ Удалено рассылок: {count}")
    
    count = await BroadcastMessage.all().count()
    await BroadcastMessage.all().delete()
    print(f"  ✓ Удалено сообщений рассылок: {count}")
    
    # Удаляем пользователей
    count = await User.all().count()
    await User.all().delete()
    print(f"\n✓ Удалено пользователей: {count}")
    
    # Удаляем админов (или оставляем одного)
    if keep_admin_id:
        admin = await Admin.get_or_none(id=keep_admin_id)
        if admin:
            count = await Admin.filter(id__ne=keep_admin_id).count()
            await Admin.filter(id__ne=keep_admin_id).delete()
            print(f"✓ Удалено админов: {count} (сохранен админ ID={keep_admin_id}: {admin.username})")
        else:
            print(f"⚠️  Админ с ID={keep_admin_id} не найден! Удаляем всех админов.")
            count = await Admin.all().count()
            await Admin.all().delete()
            print(f"✓ Удалено админов: {count}")
    else:
        count = await Admin.all().count()
        await Admin.all().delete()
        print(f"✓ Удалено админов: {count}")
    
    # Удаляем группы
    count = await AccessGroup.all().count()
    await AccessGroup.all().delete()
    print(f"✓ Удалено групп доступа: {count}")
    
    # Удаляем файлы
    count = await AccessFile.all().count()
    await AccessFile.all().delete()
    print(f"✓ Удалено файлов доступа: {count}")
    
    # Удаляем шаблоны дизайна
    count = await DesignTemplate.all().count()
    await DesignTemplate.all().delete()
    print(f"✓ Удалено шаблонов дизайна: {count}")
    
    print("\n" + "=" * 60)
    print("✅ ОЧИСТКА ЗАВЕРШЕНА!")
    print("=" * 60)
    print("\n✅ Сохранено:")
    print("  • Настройки (settings)")
    print("  • Системные данные (tariffs, statuses, durations, audiences)")
    
    if keep_admin_id:
        print(f"\n✅ Сохранен админ с ID={keep_admin_id}")
    else:
        print("\n⚠️  ВНИМАНИЕ: Все админы удалены!")
        print("   Вам нужно будет создать нового админа через API или напрямую в БД")
    
    await Tortoise.close_connections()


if __name__ == "__main__":
    keep_admin = None
    if len(sys.argv) > 1:
        try:
            keep_admin = int(sys.argv[1])
        except ValueError:
            print(f"Ошибка: '{sys.argv[1]}' не является числом")
            print("Использование: python clear_db.py [admin_id]")
            sys.exit(1)
    
    if keep_admin is None:
        print("⚠️  ВНИМАНИЕ: Будут удалены ВСЕ админы!")
        response = input("Продолжить? (yes/no): ")
        if response.lower() != "yes":
            print("Отменено.")
            sys.exit(0)
    
    asyncio.run(clear_database(keep_admin))

