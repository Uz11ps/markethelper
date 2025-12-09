#!/bin/bash

# Скрипт для исправления проблем с backend

set -e

cd /opt/markethelper

echo "🔧 Исправление проблем с backend..."

# Остановка контейнеров
echo "🛑 Остановка контейнеров..."
docker-compose down

# Проверка и создание файла базы данных
echo "💾 Проверка базы данных..."
if [ ! -f "db.sqlite3" ]; then
    touch db.sqlite3
fi
chmod 666 db.sqlite3

# Проверка прав на директории
echo "📁 Проверка прав на директории..."
mkdir -p chroma_db cookie logs
chmod -R 777 chroma_db cookie logs

# Проверка .env файла
echo "🔐 Проверка .env файла..."
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    echo "Создайте файл .env с настройками перед запуском."
    exit 1
fi

# Запуск только backend для проверки
echo "▶️  Запуск backend для проверки..."
docker-compose up -d backend

# Ожидание запуска
echo "⏳ Ожидание запуска backend (до 2 минут)..."
for i in {1..24}; do
    sleep 5
    if docker-compose exec backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/docs', timeout=2)" 2>/dev/null; then
        echo "✅ Backend запущен успешно!"
        break
    fi
    echo "   Попытка $i/24..."
done

# Проверка логов
echo ""
echo "📋 Логи backend (последние 30 строк):"
docker-compose logs --tail=30 backend

# Проверка статуса
echo ""
echo "📊 Статус контейнеров:"
docker-compose ps

# Если backend работает, запускаем остальные сервисы
if docker-compose exec backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/docs', timeout=2)" 2>/dev/null; then
    echo ""
    echo "✅ Backend работает! Запускаем остальные сервисы..."
    docker-compose up -d
    
    echo ""
    echo "✅ Все сервисы запущены!"
    echo ""
    echo "📝 Проверка работы:"
    echo "   curl http://localhost:8000/api/docs"
    echo "   curl http://localhost:8080"
else
    echo ""
    echo "❌ Backend не запустился. Проверьте логи выше."
    echo ""
    echo "Для детальной диагностики выполните:"
    echo "   docker-compose logs backend"
    echo "   docker-compose exec backend python -c 'import sys; print(sys.path)'"
fi

