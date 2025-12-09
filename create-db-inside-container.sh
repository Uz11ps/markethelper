#!/bin/bash

# Создание базы данных внутри контейнера с правильными правами

set -e

cd /opt/markethelper

echo "🔧 Создание базы данных внутри контейнера..."

# Остановка контейнеров
docker-compose down

# Создание файла через контейнер с проверкой прав
echo "💾 Создание файла базы данных..."
docker-compose run --rm backend sh -c "
    echo 'Текущий пользователь:' && whoami
    echo 'Права на /app:' && ls -ld /app
    echo 'Содержимое /app:' && ls -la /app | head -10
    echo 'Создание файла базы данных...'
    python3 << 'PYTHON'
import sqlite3
import os

db_path = '/app/db.sqlite3'
print(f'Попытка создать файл: {db_path}')
print(f'Директория существует: {os.path.exists(os.path.dirname(db_path))}')
print(f'Права на директорию: {oct(os.stat(os.path.dirname(db_path)).st_mode)}')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)')
    conn.commit()
    conn.close()
    print(f'✅ Файл создан успешно!')
    print(f'Размер файла: {os.path.getsize(db_path)} байт')
except Exception as e:
    print(f'❌ Ошибка: {e}')
    import traceback
    traceback.print_exc()
PYTHON
"

# Проверка что файл создан
echo ""
echo "📋 Проверка файла на хосте:"
if [ -f db.sqlite3 ]; then
    echo "✅ Файл существует!"
    ls -la db.sqlite3
    chmod 666 db.sqlite3
else
    echo "❌ Файл не найден на хосте!"
    echo "Пробую создать вручную..."
    touch db.sqlite3
    chmod 666 db.sqlite3
    ls -la db.sqlite3
fi

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

