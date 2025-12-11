#!/bin/bash

echo "🔍 Проверка бота на сервере..."
echo ""

echo "1. Проверка файла main_menu.py:"
docker exec markethelper-bot-prod cat /app/bot/keyboards/main_menu.py | grep -A 5 "def main_menu_kb"

echo ""
echo "2. Проверка обработчика topup:"
docker exec markethelper-bot-prod ls -la /app/bot/handlers/topup.py

echo ""
echo "3. Проверка регистрации роутеров:"
docker exec markethelper-bot-prod grep -E "(topup|keyboard_update)" /app/bot/app.py

echo ""
echo "4. Последние логи бота:"
docker logs markethelper-bot-prod --tail 20

echo ""
echo "✅ Проверка завершена!"
echo ""
echo "📱 В боте напишите: /start или /menu или /update_keyboard"

