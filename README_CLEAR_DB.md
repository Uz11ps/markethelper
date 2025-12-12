# Инструкция по очистке базы данных

## ⚠️ ВНИМАНИЕ: Это удалит всех пользователей, админов и группы!

### Вариант 1: Полная очистка (удаляет ВСЕХ админов)

```bash
# Подключитесь к контейнеру backend
docker exec -it markethelper-backend-prod bash

# Перейдите в директорию с базой данных
cd /app/data

# Выполните SQL команды
sqlite3 db.sqlite3 < /path/to/clear_database.sql

# Или выполните команды вручную:
sqlite3 db.sqlite3 <<EOF
DELETE FROM channel_bonus_requests;
DELETE FROM user_generation_settings;
DELETE FROM pending_bonuses;
DELETE FROM referral_payouts;
DELETE FROM referrals;
DELETE FROM token_purchase_requests;
DELETE FROM requests;
DELETE FROM subscriptions;
DELETE FROM ai_requests;
DELETE FROM product_descriptions;
DELETE FROM editable_prompt_templates;
DELETE FROM infographic_projects;
DELETE FROM mailings;
DELETE FROM broadcast_messages;
DELETE FROM users;
DELETE FROM admins;
DELETE FROM access_groups;
DELETE FROM access_files;
DELETE FROM design_templates;
EOF
```

### Вариант 2: Безопасная очистка (оставляет одного админа)

```bash
# Подключитесь к контейнеру backend
docker exec -it markethelper-backend-prod bash

# Перейдите в директорию с базой данных
cd /app/data

# Выполните SQL команды
sqlite3 db.sqlite3 <<EOF
DELETE FROM channel_bonus_requests;
DELETE FROM user_generation_settings;
DELETE FROM pending_bonuses;
DELETE FROM referral_payouts;
DELETE FROM referrals;
DELETE FROM token_purchase_requests;
DELETE FROM requests;
DELETE FROM subscriptions;
DELETE FROM ai_requests;
DELETE FROM product_descriptions;
DELETE FROM editable_prompt_templates;
DELETE FROM infographic_projects;
DELETE FROM mailings;
DELETE FROM broadcast_messages;
DELETE FROM users;
DELETE FROM admins WHERE id != 1;
DELETE FROM access_groups;
DELETE FROM access_files;
DELETE FROM design_templates;
EOF
```

### Вариант 3: Через Python скрипт (рекомендуется)

Создайте файл `clear_db.py` в корне проекта:

```python
import asyncio
from tortoise import Tortoise
from backend.models import (
    User, Admin, AccessGroup, Subscription, Request,
    ChannelBonusRequest, UserGenerationSettings, PendingBonus,
    ReferralPayout, Referral, TokenPurchaseRequest,
    AccessFile, AIRequest, ProductDescription, EditablePromptTemplate,
    InfographicProject, DesignTemplate, Mailing, BroadcastMessage
)

async def clear_database(keep_admin_id=None):
    """Очистка базы данных с сохранением настроек"""
    
    # Инициализация подключения
    await Tortoise.init(
        db_url="sqlite:///app/data/db.sqlite3",
        modules={"models": ["backend.models"]}
    )
    
    print("Начинаем очистку базы данных...")
    
    # Удаляем связанные данные
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
    
    # Удаляем пользователей
    await User.all().delete()
    print("✓ Пользователи удалены")
    
    # Удаляем админов (или оставляем одного)
    if keep_admin_id:
        await Admin.filter(id__ne=keep_admin_id).delete()
        print(f"✓ Админы удалены (кроме ID={keep_admin_id})")
    else:
        await Admin.all().delete()
        print("✓ Все админы удалены")
    
    # Удаляем группы
    await AccessGroup.all().delete()
    print("✓ Группы удалены")
    
    # Удаляем файлы
    await AccessFile.all().delete()
    print("✓ Файлы удалены")
    
    # Удаляем шаблоны дизайна
    await DesignTemplate.all().delete()
    print("✓ Шаблоны дизайна удалены")
    
    print("\n✅ Очистка завершена!")
    print("⚠️ Настройки (settings) сохранены")
    
    await Tortoise.close_connections()

if __name__ == "__main__":
    import sys
    keep_admin = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(clear_database(keep_admin))
```

Затем выполните:

```bash
docker exec -it markethelper-backend-prod python clear_db.py
# или чтобы оставить админа с ID=1:
docker exec -it markethelper-backend-prod python clear_db.py 1
```

## Что сохраняется:

- ✅ Таблица `settings` - все настройки из админки
- ✅ Таблица `tariffs` - системные тарифы
- ✅ Таблица `statuses` - системные статусы
- ✅ Таблица `durations` - системные длительности
- ✅ Таблица `audiences` - системные аудитории

## Что удаляется:

- ❌ Все пользователи бота
- ❌ Все администраторы (или все кроме одного)
- ❌ Все группы доступа
- ❌ Все подписки
- ❌ Все заявки
- ❌ Все файлы доступа
- ❌ Все связанные данные

