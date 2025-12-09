#!/bin/bash

# Диагностика доступа к базе данных

cd /opt/markethelper

echo "🔍 Диагностика доступа к базе данных..."
echo ""

echo "📋 Проверка файла на хосте:"
ls -la data/db.sqlite3
echo ""

echo "📋 Проверка прав на директорию data:"
ls -ld data
echo ""

echo "🔍 Проверка внутри контейнера backend:"
docker-compose exec -T backend sh << 'ENDCONTAINER'
echo "Текущий пользователь:"
whoami
echo ""
echo "Проверка директории /app/data:"
ls -la /app/data/ 2>&1 || echo "Директория не существует"
echo ""
echo "Проверка прав на директорию:"
ls -ld /app/data 2>&1 || echo "Директория не существует"
echo ""
echo "Попытка создать тестовый файл:"
touch /app/data/test.txt 2>&1 && echo "✅ Файл создан" || echo "❌ Не удалось создать файл"
rm -f /app/data/test.txt
echo ""
echo "Попытка подключиться к базе данных:"
python3 << 'PYTHON'
import sqlite3
import os

db_path = "/app/data/db.sqlite3"
print(f"Путь к БД: {db_path}")
print(f"Файл существует: {os.path.exists(db_path)}")
if os.path.exists(db_path):
    print(f"Размер файла: {os.path.getsize(db_path)} байт")
    print(f"Права на файл: {oct(os.stat(db_path).st_mode)}")
    print(f"Доступен для чтения: {os.access(db_path, os.R_OK)}")
    print(f"Доступен для записи: {os.access(db_path, os.W_OK)}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        print("✅ Подключение к БД успешно!")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
else:
    print("❌ Файл не найден!")
PYTHON
ENDCONTAINER

echo ""
echo "📋 Проверка конфигурации в коде:"
docker-compose exec backend grep -A 2 "sqlite" /app/backend/core/db.py

