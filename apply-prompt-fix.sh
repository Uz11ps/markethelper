#!/bin/bash
# Применение исправлений для генерации промпта

cd /opt/markethelper

echo "🔄 Обновление кода..."
git pull origin master

echo "🛑 Остановка bot..."
docker-compose -f docker-compose.prod.yml stop bot

echo "🔨 Пересборка bot контейнера..."
docker-compose -f docker-compose.prod.yml build --no-cache bot

echo "▶️ Запуск bot..."
docker-compose -f docker-compose.prod.yml up -d bot

echo "⏳ Ожидание запуска bot (30 секунд)..."
sleep 30

echo ""
echo "✅ Проверка работы bot:"
docker-compose -f docker-compose.prod.yml ps bot

echo ""
echo "📋 Последние логи bot (для проверки):"
docker-compose -f docker-compose.prod.yml logs --tail=20 bot

echo ""
echo "💡 Изменения:"
echo "   1. Добавлен response_format для принудительного получения JSON от GPT"
echo "   2. Улучшена обработка пустых ответов и None значений"
echo "   3. Добавлено детальное логирование для диагностики"
echo "   4. Добавлен fallback для извлечения JSON из текста"
echo "   5. Добавлена проверка наличия обязательных полей"

