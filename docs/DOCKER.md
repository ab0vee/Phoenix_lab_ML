# Docker - Контейнеризация и развертывание

## Содержание

1. [Обзор](#обзор)
2. [Сервисы Docker Compose](#сервисы-docker-compose)
3. [Конфигурация](#конфигурация)
4. [Volumes](#volumes)
5. [Networks](#networks)
6. [Запуск и управление](#запуск-и-управление)

---

## Обзор

Все сервисы Phoenix LAB контейнеризированы с помощью Docker и управляются через Docker Compose. Это обеспечивает:
- Изоляцию зависимостей
- Легкое развертывание
- Консистентное окружение
- Простое масштабирование

---

## Сервисы Docker Compose

### 1. ML Service (ml_service)

**Контейнер:** `phoenix_ml_service`

**Назначение:**
- Обработка текста локальными ML моделями
- Парафразирование и суммаризация
- Проверка схожести текстов

**Порт:** 8000

**Volumes:**
- `ml_models_cache` - кэш ML моделей

**Переменные окружения:**
- `ML_MODEL_CACHE_DIR=/app/models_cache`
- `AUTO_DOWNLOAD_MODELS=true`
- `PRELOAD_MODELS=false`
- `API_KEY` - ключ API для защиты

**Healthcheck:**
- Проверка `/health` каждые 30 секунд
- Timeout: 10 секунд
- Start period: 1200 секунд (20 минут для загрузки моделей)

**Особенности:**
- Модели кэшируются в volume для ускорения последующих запусков
- Lazy loading по умолчанию (модели загружаются при первом запросе)
- Ограничение памяти: 8GB максимум, 4GB резервация

---

### 2. Rewrite Service (rewrite_service)

**Контейнер:** `phoenix_rewrite_service`

**Назначение:**
- Основной API для рерайта статей
- Интеграция с LLM провайдерами (OpenRouter, YandexGPT)
- Управление пользователями и URL
- Публикация в Telegram

**Порт:** 5000

**Volumes:**
- `rewrite_uploads` - загруженные файлы (изображения)
- `./backend/rewrite_service/openrouter.env` - конфигурация OpenRouter
- `./backend/rewrite_service/yandex.env` - конфигурация YandexGPT
- `./backend/database` - схемы БД
- `./backend/telegram_bot/channels.json` - список каналов
- `./backend/telegram_bot/auth_tokens.json` - токены авторизации

**Переменные окружения:**
- `PORT=5000`
- `ML_SERVICE_URL=http://ml_service:8000`
- `DATABASE_URL` - подключение к PostgreSQL
- `API_KEY` - ключ API

**Зависимости:**
- `ml_service` - для обработки текста
- `postgres` - база данных

**Healthcheck:**
- Проверка `/api/health` каждые 30 секунд

---

### 3. Telegram Bot (telegram_bot)

**Контейнер:** `phoenix_telegram_bot`

**Назначение:**
- Управление Telegram каналами
- Авторизация пользователей
- Отправка статей в каналы

**Volumes:**
- `telegram_bot_data` - данные бота
- `./backend/telegram_bot/channels.json` - список каналов
- `./backend/telegram_bot/auth_tokens.json` - токены авторизации

**Переменные окружения:**
- `API_URL=http://rewrite_service:5000` - URL Rewrite Service
- `BOT_TOKEN` - токен Telegram бота

**Зависимости:**
- `rewrite_service` - для отправки статей

**Особенности:**
- Бот автоматически перезапускается при ошибках
- Каналы и токены синхронизируются с Rewrite Service

---

### 4. Frontend (frontend)

**Контейнер:** `phoenix_frontend`

**Назначение:**
- Веб-интерфейс для работы с системой
- Управление контентом
- Настройки и мониторинг

**Порт:** 3000

**Build args:**
- `NEXT_PUBLIC_API_URL=http://localhost:5000` - URL Rewrite Service (для браузера)
- `NEXT_PUBLIC_ML_SERVICE_URL=http://localhost:8000` - URL ML Service (для браузера)

**Переменные окружения:**
- `NODE_ENV=production`

**Зависимости:**
- `rewrite_service` - для API запросов
- `ml_service` - для прямой связи с ML Service (опционально)

**Healthcheck:**
- Проверка доступности на порту 3000

**Особенности:**
- Next.js собирается в production режиме
- Статические файлы оптимизированы
- SSR для быстрой загрузки

---

### 5. PostgreSQL (postgres)

**Контейнер:** `phoenix_postgres`

**Назначение:**
- База данных для пользователей и URL
- Хранение результатов обработки

**Порт:** 5432

**Volumes:**
- `postgres_data` - данные PostgreSQL

**Переменные окружения:**
- `POSTGRES_USER=phoenix_user`
- `POSTGRES_PASSWORD=phoenix_password`
- `POSTGRES_DB=phoenix_lab`

**Healthcheck:**
- Проверка через `pg_isready` каждые 10 секунд

**Особенности:**
- Использует Alpine образ для меньшего размера
- Данные персистентны в volume
- Автоматическая инициализация базы данных

---

### 6. Redis (redis)

**Контейнер:** `phoenix_redis`

**Назначение:**
- Кэширование результатов обработки
- Очереди задач (для будущего использования)

**Порт:** 6379

**Volumes:**
- `redis_data` - данные Redis

**Команда:**
- `redis-server --appendonly yes` - включение AOF для персистентности

**Healthcheck:**
- Проверка через `redis-cli ping` каждые 10 секунд

**Особенности:**
- AOF включен для надежности
- Данные персистентны в volume
- Быстрый доступ к кэшу

---

## Конфигурация

### docker-compose.yml

Основной файл конфигурации содержит все сервисы и их настройки.

**Структура:**
```yaml
services:
  ml_service: ...
  rewrite_service: ...
  telegram_bot: ...
  frontend: ...
  postgres: ...
  redis: ...

networks:
  phoenix_network: ...

volumes:
  ml_models_cache: ...
  rewrite_uploads: ...
  telegram_bot_data: ...
  postgres_data: ...
  redis_data: ...
```

### Переменные окружения

Переменные окружения задаются через:
1. `.env` файл (для общих переменных)
2. `env_file` в docker-compose.yml
3. `environment` в docker-compose.yml

**Пример:**
```yaml
environment:
  - API_KEY=${API_KEY:-your-api-key-here}
env_file:
  - .env
```

---

## Volumes

### ml_models_cache

**Назначение:** Кэш ML моделей

**Использование:**
- Модели скачиваются один раз и кэшируются
- Ускоряет последующие запуски
- Экономит трафик

**Размер:** ~5-10 GB (зависит от моделей)

---

### rewrite_uploads

**Назначение:** Загруженные файлы (изображения)

**Использование:**
- Изображения из статей
- Сгенерированные изображения
- Загруженные пользователями

---

### telegram_bot_data

**Назначение:** Данные Telegram бота

**Использование:**
- Временные файлы бота
- Кэш данных

---

### postgres_data

**Назначение:** Данные PostgreSQL

**Использование:**
- Все таблицы базы данных
- Индексы
- Конфигурация

**Важно:** Этот volume содержит все данные БД. При удалении volume все данные будут потеряны!

---

### redis_data

**Назначение:** Данные Redis

**Использование:**
- Кэшированные данные
- Очереди задач

---

## Networks

### phoenix_network

**Тип:** bridge

**Назначение:**
- Связь между всеми контейнерами
- Изоляция от других Docker сетей

**Использование:**
- Все сервисы подключены к одной сети
- Доступ друг к другу по именам контейнеров
- Например: `http://ml_service:8000`

---

## Запуск и управление

### Запуск всех сервисов

```bash
docker-compose up -d --build
```

**Опции:**
- `-d` - запуск в фоновом режиме
- `--build` - пересборка образов

---

### Остановка всех сервисов

```bash
docker-compose down
```

**Опции:**
- `-v` - удаление volumes (осторожно!)
- `--remove-orphans` - удаление orphan контейнеров

---

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f ml_service
```

---

### Перезапуск сервиса

```bash
docker-compose restart ml_service
```

---

### Обновление конфигурации

```bash
# Остановка
docker-compose down

# Обновление .env файла

# Запуск с пересборкой
docker-compose up -d --build
```

---

### Просмотр статуса

```bash
docker-compose ps
```

---

### Выполнение команд в контейнере

```bash
# Bash в контейнере
docker-compose exec ml_service bash

# Python в контейнере
docker-compose exec rewrite_service python
```

---

## Особенности

### Первый запуск

При первом запуске:
1. ML Service скачивает модели (~5-10 GB) - может занять 10-30 минут
2. PostgreSQL инициализирует базу данных
3. Frontend собирается в production режиме

**Рекомендации:**
- Убедитесь в наличии свободного места на диске (~15 GB)
- Дождитесь завершения загрузки моделей перед использованием

---

### Проблемы и решения

**Проблема:** Контейнер не запускается
**Решение:** Проверьте логи `docker-compose logs <service_name>`

**Проблема:** Модели не загружаются
**Решение:** Проверьте `AUTO_DOWNLOAD_MODELS=true` и наличие интернета

**Проблема:** БД недоступна
**Решение:** Убедитесь, что PostgreSQL контейнер запущен и прошел healthcheck

**Проблема:** Высокое использование памяти
**Решение:** Уменьшите `PRELOAD_MODELS` или ограничьте память для ML Service

---

## Заключение

Docker Compose упрощает развертывание и управление всеми сервисами Phoenix LAB. Все сервисы изолированы, но могут взаимодействовать через внутреннюю сеть, что обеспечивает безопасность и производительность.

