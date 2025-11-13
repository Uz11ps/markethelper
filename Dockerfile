FROM python:3.12-slim

# Рабочая директория
WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# По умолчанию (для docker-compose укажем разные команды)
CMD ["python", "--version"]
