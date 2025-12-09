# Настройка переменных окружения (.env)

## Как изменить BOT_USERNAME в .env файле

### Способ 1: Через скрипт (рекомендуется)

```bash
cd /opt/markethelper
git pull origin master
chmod +x update-bot-username.sh
./update-bot-username.sh fghghhjgk_bot
```

Скрипт автоматически:
- Обновит или добавит `BOT_USERNAME` в `.env`
- Перезапустит backend для применения изменений

### Способ 2: Вручную через редактор

```bash
cd /opt/markethelper

# Откройте .env файл в редакторе
nano .env
# или
vi .env
```

Добавьте или измените строку:
```bash
BOT_USERNAME=fghghhjgk_bot
```

Сохраните файл (в nano: `Ctrl+O`, `Enter`, `Ctrl+X`)

Затем перезапустите backend:
```bash
docker-compose -f docker-compose.prod.yml restart backend
```

### Способ 3: Через echo (быстрый способ)

```bash
cd /opt/markethelper

# Если BOT_USERNAME уже есть в .env, обновляем
sed -i 's/^BOT_USERNAME=.*/BOT_USERNAME=fghghhjgk_bot/' .env

# Если BOT_USERNAME нет, добавляем
if ! grep -q "^BOT_USERNAME=" .env; then
    echo "BOT_USERNAME=fghghhjgk_bot" >> .env
fi

# Перезапускаем backend
docker-compose -f docker-compose.prod.yml restart backend
```

## Структура .env файла

Пример полного `.env` файла:

```bash
# Telegram Bot Configuration
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
BOT_USERNAME=fghghhjgk_bot

# Backend Configuration
BACKEND_URL=http://backend:8000

# OpenAI API
OPENAI_API_KEY=sk-...

# FAL AI Configuration
FAL_API_KEY=your_fal_api_key_here

# JWT Secret Key (для админ-панели)
JWT_SECRET_KEY=your-secret-key-change-this-in-production
```

## Важные переменные

| Переменная | Описание | Пример |
|------------|----------|--------|
| `BOT_TOKEN` | Токен Telegram бота | `1234567890:ABC...` |
| `BOT_USERNAME` | Имя бота (без @) для реферальных ссылок | `fghghhjgk_bot` |
| `BACKEND_URL` | URL backend API | `http://backend:8000` |
| `OPENAI_API_KEY` | API ключ OpenAI | `sk-...` |
| `FAL_API_KEY` | API ключ FAL AI | `...` |
| `JWT_SECRET_KEY` | Секретный ключ для JWT токенов | `your-secret-key` |

## Проверка текущих значений

```bash
# Показать все переменные из .env
cat .env

# Показать только BOT_USERNAME
grep "^BOT_USERNAME=" .env

# Показать все переменные окружения в контейнере backend
docker-compose -f docker-compose.prod.yml exec backend env | grep BOT
```

## Применение изменений

После изменения `.env` файла нужно перезапустить соответствующие сервисы:

```bash
# Перезапуск только backend
docker-compose -f docker-compose.prod.yml restart backend

# Перезапуск только bot
docker-compose -f docker-compose.prod.yml restart bot

# Перезапуск всех сервисов
docker-compose -f docker-compose.prod.yml restart
```

## Безопасность

⚠️ **Важно:** Файл `.env` содержит секретные данные и не должен попадать в Git!

- Файл `.env` уже добавлен в `.gitignore`
- Не коммитьте `.env` в репозиторий
- Используйте `.env.example` как шаблон

## Примеры использования

### Изменить имя бота на другой:
```bash
./update-bot-username.sh my_new_bot_name
```

### Проверить текущее имя бота:
```bash
grep "^BOT_USERNAME=" .env
```

### Удалить BOT_USERNAME из .env (вернется к значению по умолчанию):
```bash
sed -i '/^BOT_USERNAME=/d' .env
docker-compose -f docker-compose.prod.yml restart backend
```

