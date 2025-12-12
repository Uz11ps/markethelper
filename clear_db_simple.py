#!/usr/bin/env python3
"""
Простой скрипт для очистки базы данных (работает внутри контейнера)
"""
import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, '/app')

from tortoise import Tortoise
from backend.models import (
    User, Admin, AccessGroup, Subscription, Request,
    UserGenerationSettings, PendingBonus,
    ReferralPayout, Referral, TokenPurchaseRequest,
    AccessFile, AIRequest, ProductDescription, EditablePromptTemplate,
    InfographicProject, DesignTemplate, Mailing, BroadcastMessage
)
from backend.models.channel_bonus import ChannelBonusRequest

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
    
    await Tortoise.init(config=TORTOISE_ORM)
    
    print("=" * 60)
    print("ОЧИСТКА БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    if keep_admin_id:
        print(f"Сохраняем админа с ID={keep_admin_id}")
    else:
        print("Удаляем ВСЕХ админов!")
    
    print("\nУдаление данных...")
    
    await ChannelBonusRequest.all().delete()
    await UserGenerationSettings.all().delete()
    await PendingBonus.all().delete()
    await ReferralPayout.all().delete()
    await Referral.all().delete()
    await TokenPurchaseRequest.all().delete()
    await Request.all().delete()
    await Subscription.all().delete()
    await AIRequest.all().delete()
    await ProductDescription.all().delete()
    await EditablePromptTemplate.all().delete()
    await InfographicProject.all().delete()
    await Mailing.all().delete()
    await BroadcastMessage.all().delete()
    
    count = await User.all().count()
    await User.all().delete()
    print(f"✓ Удалено пользователей: {count}")
    
    if keep_admin_id:
        admin = await Admin.get_or_none(id=keep_admin_id)
        if admin:
            count = await Admin.filter(id__ne=keep_admin_id).count()
            await Admin.filter(id__ne=keep_admin_id).delete()
            print(f"✓ Удалено админов: {count} (сохранен: {admin.username})")
        else:
            print(f"⚠ Админ ID={keep_admin_id} не найден!")
            count = await Admin.all().count()
            await Admin.all().delete()
            print(f"✓ Удалено админов: {count}")
    else:
        count = await Admin.all().count()
        await Admin.all().delete()
        print(f"✓ Удалено админов: {count}")
    
    count = await AccessGroup.all().count()
    await AccessGroup.all().delete()
    print(f"✓ Удалено групп: {count}")
    
    count = await AccessFile.all().count()
    await AccessFile.all().delete()
    print(f"✓ Удалено файлов: {count}")
    
    count = await DesignTemplate.all().count()
    await DesignTemplate.all().delete()
    print(f"✓ Удалено шаблонов: {count}")
    
    print("\n✅ ГОТОВО! Настройки сохранены.")
    
    await Tortoise.close_connections()


if __name__ == "__main__":
    keep_admin = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(clear_database(keep_admin))

