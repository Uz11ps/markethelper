#!/bin/bash

# Скрипт для правильного применения изменений на сервере

echo "🔍 Проверка текущей ветки..."
cd /opt/markethelper
git branch

echo ""
echo "📥 Получение последних изменений из main..."
git pull github main

echo ""
echo "⏹️  Остановка контейнеров..."
docker-compose -f docker-compose.prod.yml down

echo ""
echo "🔨 Пересборка и запуск контейнеров (это займет несколько минут)..."
docker-compose -f docker-compose.prod.yml up -d --build

echo ""
echo "⏳ Ожидание запуска сервисов (10 секунд)..."
sleep 10

echo ""
echo "📊 Проверка статуса контейнеров..."
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "📋 Последние логи бота:"
docker logs markethelper-bot-prod --tail 20

echo ""
echo "✅ Готово! Проверьте:"
echo "   1. Бот: нажмите /start или /menu в боте"
echo "   2. Группы: откройте https://iawuuw.com/groups.html"

