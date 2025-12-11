# Инструкция по развертыванию на сервере

## Важно: Используется ветка `main`

Все изменения теперь пушатся в ветку `main` на GitHub.

## Быстрое применение изменений

```bash
# 1. Подключитесь к серверу
ssh root@iawuuw.com

# 2. Перейдите в директорию проекта
cd /opt/markethelper

# 3. Получите последние изменения из ветки main
git pull github main

# 4. Перезапустите контейнеры (ОБЯЗАТЕЛЬНО после изменений в коде!)
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# 5. Проверьте статус
docker-compose -f docker-compose.prod.yml ps
```

## Когда нужно перезапускать

**ОБЯЗАТЕЛЬНО перезапускать после:**
- Изменений в коде бота (`bot/`)
- Изменений в коде backend (`backend/`)
- Изменений в frontend (`frontend/`)
- Обновления зависимостей (`requirements.txt`)
- Изменений в Dockerfile

**Можно просто перезапустить без rebuild:**
```bash
docker-compose -f docker-compose.prod.yml restart bot
docker-compose -f docker-compose.prod.yml restart backend
docker-compose -f docker-compose.prod.yml restart frontend
```

**Полный перезапуск с пересборкой (рекомендуется после git pull):**
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

## Проверка логов

```bash
# Логи бота
docker logs markethelper-bot-prod --tail 50 -f

# Логи backend
docker logs markethelper-backend-prod --tail 50 -f

# Логи frontend
docker logs markethelper-frontend-prod --tail 50 -f

# Все логи
docker-compose -f docker-compose.prod.yml logs -f
```

## Структура проекта на сервере

- **Директория:** `/opt/markethelper`
- **Ветка:** `main` (или `master` для совместимости)
- **Remote:** `github` → `https://github.com/Uz11ps/markethelper.git`

## Настройка на сервере (если нужно)

Если на сервере еще нет правильного remote:

```bash
cd /opt/markethelper
git remote add github https://github.com/Uz11ps/markethelper.git
git fetch github
git checkout main || git checkout -b main github/main
```

## Автоматический скрипт развертывания

Можно создать скрипт `/opt/markethelper/deploy.sh`:

```bash
#!/bin/bash
cd /opt/markethelper
git pull github main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
echo "✅ Развертывание завершено!"
```

Сделать исполняемым:
```bash
chmod +x /opt/markethelper/deploy.sh
```

Использование:
```bash
/opt/markethelper/deploy.sh
```

