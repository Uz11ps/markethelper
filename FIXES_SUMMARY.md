# Исправления проблем

## Что было исправлено

### 1. Рассылка на всех пользователей показывает "Получатели: 0"
**Проблема:** Frontend использовал неправильный endpoint и параметры
**Исправление:**
- Изменен endpoint с `/api/admin/broadcast` на `/api/admin/broadcast/send`
- Изменен параметр с `audience` на `target`
- Добавлена правильная обработка ответа с `sent_count`

### 2. Рассылка на активных пользователей выдает ошибку 500
**Проблема:** Неправильная фильтрация подписок по статусу
**Исправление:**
- Исправлена фильтрация активных подписок через `status_id` вместо `status__code`
- Добавлена поддержка фильтрации неактивных пользователей
- Добавлено подробное логирование для отладки

### 3. Продление подписки выдает ошибку 500
**Проблема:** Endpoint не существовал в админ-роутере
**Исправление:**
- Создан новый файл `backend/api/admin_subscriptions.py`
- Добавлен endpoint `/api/admin/subscriptions/{id}/extend`
- Исправлено использование `status_id` вместо `status`
- Добавлена обработка ошибок и логирование

### 4. Дублирование API_BASE_URL
**Проблема:** Переменная объявлялась в каждом JS файле
**Исправление:**
- Убрано дублирование из всех файлов кроме `auth.js`
- Все файлы теперь используют общую переменную из `auth.js`

## Применение исправлений

```bash
cd /opt/markethelper

# Обновите код
git pull origin master

# Запустите скрипт исправления
chmod +x fix-all-issues.sh
./fix-all-issues.sh
```

Или вручную:

```bash
cd /opt/markethelper
git pull origin master

# Добавьте переменные в .env если их нет
if ! grep -q "^BOT_USERNAME=" .env; then
    echo "BOT_USERNAME=fghghhjgk_bot" >> .env
fi
if ! grep -q "^BOT_API_URL=" .env; then
    echo "BOT_API_URL=http://bot:8001" >> .env
fi

# Перезапустите сервисы
docker-compose -f docker-compose.prod.yml restart backend bot frontend
```

## Проверка работы

1. **Рассылка на всех:**
   - Откройте админ-панель → Активные подписки
   - Введите сообщение и выберите "Все пользователи"
   - Должно показать правильное количество получателей

2. **Рассылка на активных:**
   - Выберите "Активные подписки"
   - Должно работать без ошибок

3. **Продление подписки:**
   - Нажмите "Продлить" на любой подписке
   - Введите количество дней
   - Должно работать без ошибок

## Отладка

Если проблемы остаются, проверьте логи:

```bash
# Логи backend
docker-compose -f docker-compose.prod.yml logs --tail=50 backend | grep -i "broadcast\|extend\|error"

# Логи bot
docker-compose -f docker-compose.prod.yml logs --tail=50 bot | grep -i "error"
```

## Переменные окружения

Убедитесь, что в `.env` есть:
- `BOT_USERNAME=fghghhjgk_bot` - для реферальных ссылок
- `BOT_API_URL=http://bot:8001` - для рассылки
- `BOT_TOKEN=...` - токен бота
- `BACKEND_URL=http://backend:8000` - URL backend для бота

