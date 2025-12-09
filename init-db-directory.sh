#!/bin/bash

# Создание директории для базы данных

set -e

cd /opt/markethelper

echo "🔧 Создание директории для базы данных..."

# Остановка контейнеров
docker-compose down

# Создание директории data
mkdir -p data
chmod 777 data

# Создание файла базы данных в директории data
echo "💾 Создание файла базы данных..."
python3 << 'EOF'
import sqlite3
import os

os.makedirs('data', exist_ok=True)
db_path = 'data/db.sqlite3'
conn = sqlite3.connect(db_path)
conn.close()
print(f"✅ Файл создан: {db_path}")
EOF

# Установка прав
chmod 666 data/db.sqlite3
chmod 777 data

# Проверка
echo ""
echo "📋 Проверка:"
ls -la data/

# Обновление docker-compose.yml
cp docker-compose.prod.yml docker-compose.yml

# Запуск контейнеров
echo ""
echo "▶️  Запуск контейнеров..."
docker-compose up -d

# Ожидание
echo "⏳ Ожидание запуска (15 секунд)..."
sleep 15

# Проверка логов
echo ""
echo "📋 Логи backend:"
docker-compose logs --tail=30 backend

