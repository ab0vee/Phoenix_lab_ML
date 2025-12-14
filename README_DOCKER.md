# Phoenix LAB - Запуск через Docker Compose

## Быстрый старт

1. **Создайте файл `.env` в корне проекта** (скопируйте из `.env.example` и заполните):

```bash
# API ключи
API_KEY=your-api-key-here  # Должен совпадать для ml_service и rewrite_service

# OpenRouter (для Qwen)
OPENROUTER_API_KEY=your-openrouter-api-key

# YandexGPT (для Yandex Alice)
YANDEX_CLOUD_API_KEY=your-yandex-api-key
YANDEX_CLOUD_PROJECT=your-project-id

# Telegram Bot
BOT_TOKEN=your-telegram-bot-token

# Pexels (для поиска изображений)
PEXELS_API_KEY=your-pexels-api-key

# FusionBrain/Kandinsky (для генерации изображений)
FUSIONBRAIN_API_KEY=your-fusionbrain-api-key
FUSIONBRAIN_SECRET_KEY=your-fusionbrain-secret-key
```

2. **Запустите все сервисы:**

```bash
docker-compose up -d
```

3. **Проверьте статус:**

```bash
docker-compose ps
```

4. **Откройте в браузере:**

- Frontend: http://localhost:3000
- ML Service API: http://localhost:8000
- Rewrite Service API: http://localhost:5000
- PostgreSQL: localhost:5432

## Остановка сервисов

```bash
docker-compose down
```

## Пересборка после изменений

```bash
# Пересобрать все сервисы
docker-compose up -d --build

# Пересобрать конкретный сервис
docker-compose up -d --build frontend
docker-compose up -d --build rewrite_service
docker-compose up -d --build ml_service
```

## Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f frontend
docker-compose logs -f rewrite_service
docker-compose logs -f ml_service
docker-compose logs -f telegram_bot
```

## Структура сервисов

- **frontend** (порт 3000) - Next.js приложение
- **rewrite_service** (порт 5000) - Flask API для рерайта статей
- **ml_service** (порт 8000) - FastAPI для ML моделей (RUT5, FLAN-T5, Gazeta)
- **telegram_bot** - Telegram бот для авторизации
- **postgres** (порт 5432) - PostgreSQL база данных
- **redis** (порт 6379) - Redis для кэширования

## Переменные окружения

### Frontend
- `NEXT_PUBLIC_API_URL` - URL для Rewrite Service (по умолчанию: http://localhost:5000)
- `NEXT_PUBLIC_ML_SERVICE_URL` - URL для ML Service (по умолчанию: http://localhost:8000)

### Rewrite Service
- `ML_SERVICE_URL` - URL ML Service внутри Docker сети (http://ml_service:8000)
- `API_KEY` - API ключ для доступа к ML Service
- `DATABASE_URL` - URL базы данных PostgreSQL

### ML Service
- `API_KEY` - API ключ (должен совпадать с rewrite_service)
- `PRELOAD_MODELS` - Предзагрузка моделей при старте (false = lazy loading)
- `ML_DEVICE` - Устройство для ML (cpu/cuda)

## Volumes (постоянное хранение)

- `ml_models_cache` - Кэш ML моделей (чтобы не скачивать каждый раз)
- `rewrite_uploads` - Загруженные изображения
- `telegram_bot_data` - Данные Telegram бота
- `postgres_data` - Данные PostgreSQL
- `redis_data` - Данные Redis

## Troubleshooting

### Проблема: Frontend не может подключиться к API

**Решение:** Убедитесь, что:
- Rewrite Service запущен: `docker-compose ps rewrite_service`
- Порт 5000 не занят другим приложением
- В браузере открывается http://localhost:5000/api/health

### Проблема: ML Service не отвечает

**Решение:**
- Проверьте логи: `docker-compose logs ml_service`
- Модели загружаются при первом запросе (может занять 1-2 минуты)
- Убедитесь, что `API_KEY` совпадает в обоих сервисах

### Проблема: База данных недоступна

**Решение:**
- Проверьте, что PostgreSQL запущен: `docker-compose ps postgres`
- Проверьте логи: `docker-compose logs postgres`
- Убедитесь, что `DATABASE_URL` правильный в rewrite_service

### Проблема: Модели не загружаются

**Решение:**
- Проверьте объем диска (модели занимают ~2-3 GB)
- Проверьте интернет-соединение (модели скачиваются с Hugging Face)
- Проверьте логи: `docker-compose logs ml_service`

## Разработка

Для разработки можно запускать сервисы локально (без Docker) или использовать Docker только для некоторых сервисов.

### Запуск только БД и Redis в Docker:

```bash
docker-compose up -d postgres redis
```

Затем запускайте frontend и backend локально.



