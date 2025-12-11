# СРОЧНОЕ ИСПРАВЛЕНИЕ

## Проблема
После `restart` изменения не применяются, потому что контейнеры не пересобираются.

## Решение

На сервере выполните:

```bash
cd /opt/markethelper

# 1. Убедитесь, что код обновлен
git pull github main

# 2. ОБЯЗАТЕЛЬНО используйте down и up --build (не restart!)
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# 3. Проверьте логи бота
docker logs markethelper-bot-prod --tail 50

# 4. В боте нажмите /start или /menu для обновления клавиатуры
```

## Почему restart не работает?

`docker-compose restart` только перезапускает контейнеры с **старым кодом внутри**. 
`docker-compose up --build` **пересобирает образы** с новым кодом.

## Проверка что код обновился

```bash
# Проверьте что файл обновился в контейнере
docker exec markethelper-bot-prod cat /app/bot/keyboards/main_menu.py | grep "Пополнить"

# Должно быть:
# [KeyboardButton(text="💰 Пополнить")],
```

## Если все еще не работает

1. Проверьте логи:
```bash
docker logs markethelper-bot-prod --tail 100
```

2. Проверьте что обработчик зарегистрирован:
```bash
docker exec markethelper-bot-prod grep -r "topup.router" /app/bot/
```

3. Пересоберите с очисткой кэша:
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

