# Как посмотреть логи бота

## Вариант 1: Если бот запущен в Docker (на сервере)

### Подключитесь к серверу по SSH:
```bash
ssh user@your-server
```

### Посмотреть логи бота в реальном времени:
```bash
docker logs -f markethelper-bot
```

### Посмотреть последние 100 строк логов:
```bash
docker logs --tail 100 markethelper-bot
```

### Посмотреть логи с фильтрацией по ключевому слову:
```bash
docker logs markethelper-bot 2>&1 | grep "generate_mode_handler"
```

### Посмотреть логи за последние 10 минут:
```bash
docker logs --since 10m markethelper-bot
```

## Вариант 2: Если используете docker-compose

### Посмотреть логи бота:
```bash
docker-compose logs -f bot
```

### Посмотреть логи всех сервисов:
```bash
docker-compose logs -f
```

### Посмотреть последние 100 строк логов бота:
```bash
docker-compose logs --tail 100 bot
```

## Вариант 3: Если бот запущен локально (без Docker)

Логи выводятся в консоль, где запущен бот. Если запускаете через:
```bash
python -m bot.app
```

То логи будут видны в этой же консоли.

## Поиск конкретных ошибок

### Найти все ошибки в логах:
```bash
docker logs markethelper-bot 2>&1 | grep -i "error\|exception\|traceback"
```

### Найти логи конкретного обработчика:
```bash
docker logs markethelper-bot 2>&1 | grep "generate_mode_handler"
```

### Сохранить логи в файл:
```bash
docker logs markethelper-bot > bot_logs.txt
```

## Полезные команды для диагностики

### Проверить, запущен ли контейнер бота:
```bash
docker ps | grep markethelper-bot
```

### Перезапустить бота и сразу посмотреть логи:
```bash
docker restart markethelper-bot && docker logs -f markethelper-bot
```

### Посмотреть логи бота и бэкенда одновременно:
```bash
docker logs -f markethelper-bot markethelper-backend
```

