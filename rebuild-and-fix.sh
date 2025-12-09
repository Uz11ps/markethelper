#!/bin/bash

# Пересборка контейнеров и исправление проблемы с БД

set -e

cd /opt/markethelper

echo "🔧 Пересборка контейнеров с обновленным кодом..."

# Остановка контейнеров
echo "🛑 Остановка контейнеров..."
docker-compose down

# Обновление кода
echo "📥 Обновление кода..."
git pull origin master

# Проверка что файл БД существует
echo "💾 Проверка файла базы данных..."
if [ ! -f "data/db.sqlite3" ]; then
    echo "Создание файла базы данных..."
    mkdir -p data
    python3 -c "import sqlite3; conn = sqlite3.connect('data/db.sqlite3'); conn.close()"
    chmod 666 data/db.sqlite3
    chmod 777 data
fi

# Обновление docker-compose.yml
cp docker-compose.prod.yml docker-compose.yml

# Пересборка контейнеров
echo "🔨 Пересборка контейнеров..."
docker-compose build --no-cache backend

# Запуск контейнеров
echo "▶️  Запуск контейнеров..."
docker-compose up -d

# Ожидание
echo "⏳ Ожидание запуска (20 секунд)..."
sleep 20

# Проверка логов
echo ""
echo "📋 Логи backend (последние 30 строк):"
docker-compose logs --tail=30 backend

# Проверка статуса
echo ""
echo "📊 Статус контейнеров:"
docker-compose ps

# Проверка доступа к БД внутри контейнера
echo ""
echo "🔍 Проверка доступа к БД внутри контейнера:"
docker-compose exec -T backend python3 << 'PYTHON'
import sqlite3
import os

db_path = "/app/data/db.sqlite3"
print(f"Путь к БД: {db_path}")
print(f"Файл существует: {os.path.exists(db_path)}")
if os.path.exists(db_path):
    print(f"Размер: {os.path.getsize(db_path)} байт")
    try:
        conn = sqlite3.connect(db_path)
        conn.close()
        print("✅ База данных доступна!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
else:
    print("❌ Файл не найден!")
PYTHON

echo ""
echo "✅ Проверка завершена!"

