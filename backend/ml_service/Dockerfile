# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Создаём рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Устанавливаем PyTorch CPU версию (меньше размер)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Копируем код приложения
COPY . .

# Создаём директорию для кэша моделей
RUN mkdir -p /app/models_cache

# Открываем порт
EXPOSE 8000

# Переменные окружения по умолчанию
ENV PYTHONUNBUFFERED=1
ENV ML_MODEL_CACHE_DIR=/app/models_cache
ENV HF_HOME=/app/models_cache
ENV TRANSFORMERS_CACHE=/app/models_cache
ENV HF_DATASETS_CACHE=/app/models_cache
ENV AUTO_DOWNLOAD_MODELS=True
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Запуск приложения
CMD ["python", "main.py"]
