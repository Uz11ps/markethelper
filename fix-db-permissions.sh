#!/bin/bash

# Скрипт для исправления прав доступа к базе данных

set -e

cd /opt/markethelper

echo "🔧 Исправление прав доступа к базе данных..."

# Остановка контейнеров
echo "🛑 Остановка контейнеров..."
docker-compose down

# Создание файла базы данных с правильными правами
echo "💾 Создание файла базы данных..."
if [ -f "db.sqlite3" ]; then
    echo "Файл уже существует, обновляю права..."
else
    echo "Создаю новый файл..."
    touch db.sqlite3 || {
        echo "Ошибка создания файла, пробую через Python..."
        python3 -c "open('db.sqlite3', 'a').close()" || {
            echo "Ошибка создания через Python, пробую через sqlite3..."
            sqlite3 db.sqlite3 "SELECT 1;" 2>/dev/null || touch db.sqlite3
        }
    }
fi

chmod 666 db.sqlite3

# Проверка прав
echo "📋 Проверка прав на файл:"
if [ -f "db.sqlite3" ]; then
    ls -la db.sqlite3
else
    echo "❌ Файл все еще не создан!"
    echo "Пробую создать через другой метод..."
    echo "" > db.sqlite3
    chmod 666 db.sqlite3
    ls -la db.sqlite3
fi

# Проверка прав на директорию
echo "📋 Проверка прав на директорию:"
ls -ld /opt/markethelper

# Создание директорий если их нет
echo "📁 Создание необходимых директорий..."
mkdir -p chroma_db cookie logs
chmod -R 777 chroma_db cookie logs

# Проверка что файл существует и доступен
if [ -f "db.sqlite3" ]; then
    echo "✅ Файл db.sqlite3 существует"
    echo "📋 Информация о файле:"
    ls -la db.sqlite3
    file db.sqlite3
else
    echo "❌ Файл db.sqlite3 не найден!"
    exit 1
fi

# Попытка создать тестовую запись в базе данных через Python
echo "🧪 Тестирование доступа к базе данных..."
docker-compose run --rm backend python << 'PYTHON'
import sqlite3
import os

db_path = "/app/db.sqlite3"
print(f"Проверка доступа к: {db_path}")
print(f"Файл существует: {os.path.exists(db_path)}")
print(f"Права на файл: {oct(os.stat(db_path).st_mode)}")
print(f"Доступен для чтения: {os.access(db_path, os.R_OK)}")
print(f"Доступен для записи: {os.access(db_path, os.W_OK)}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()
    print("✅ База данных доступна для записи!")
except Exception as e:
    print(f"❌ Ошибка доступа к базе данных: {e}")
PYTHON

echo ""
echo "✅ Проверка завершена!"
echo ""
echo "▶️  Запуск контейнеров..."
docker-compose up -d

echo "⏳ Ожидание запуска (10 секунд)..."
sleep 10

echo "📋 Логи backend:"
docker-compose logs --tail=30 backend

