#!/bin/bash
# Применение исправлений для редактирования баланса и получения файла куков

cd /opt/markethelper

echo "🔄 Обновление кода..."
git pull origin master

echo "🛑 Остановка backend..."
docker-compose -f docker-compose.prod.yml stop backend

echo "🔨 Пересборка backend контейнера..."
docker-compose -f docker-compose.prod.yml build --no-cache backend

echo "▶️ Запуск backend..."
docker-compose -f docker-compose.prod.yml up -d backend

echo "⏳ Ожидание запуска backend (40 секунд)..."
sleep 40

echo ""
echo "✅ Проверка работы backend:"
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/docs)

if [ "$response" = "200" ]; then
    echo "✅ Backend работает (HTTP $response)"
else
    echo "⚠️ Backend вернул код (HTTP $response)"
fi

echo ""
echo "📋 Статус контейнеров:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "💡 Изменения:"
echo "   1. Исправлена ошибка получения файла куков - теперь можно получить файл даже без активной подписки"
echo "   2. Добавлена возможность редактирования баланса пользователя в таблице 'Активные подписки'"
echo "   3. В таблице добавлена колонка 'Баланс' с кнопкой 'Изменить'"

