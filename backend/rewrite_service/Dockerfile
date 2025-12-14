# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаём рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаём директорию для загрузок
RUN mkdir -p /app/uploads

# Открываем порт
EXPOSE 5000

# Переменные окружения по умолчанию
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=server.py
ENV FLASK_ENV=production
ENV PORT=5000

# Запуск приложения
CMD ["python", "server.py"]

