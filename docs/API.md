# API Документация - Все эндпоинты и зависимости

## Содержание

1. [Обзор](#обзор)
2. [Rewrite Service API (Flask)](#rewrite-service-api-flask)
3. [ML Service API (FastAPI)](#ml-service-api-fastapi)
4. [Внешние API зависимости](#внешние-api-зависимости)
5. [Аутентификация](#аутентификация)
6. [Примеры использования](#примеры-использования)

---

## Обзор

Система состоит из двух основных API сервисов:

1. **Rewrite Service (Flask)** - порт 5000
   - Основной API для рерайта статей
   - Интеграция с LLM провайдерами
   - Управление пользователями и URL
   - Публикация в Telegram

2. **ML Service (FastAPI)** - порт 8000
   - Обработка текста локальными ML моделями
   - Парафразирование и суммаризация
   - Проверка схожести текстов

---

## Rewrite Service API (Flask)

Базовый URL: `http://localhost:5000`

### Health Check

**GET** `/api/health`

Проверка работоспособности сервиса.

**Ответ:**
```json
{
    "status": "ok",
    "service": "rewrite_service"
}
```

---

### Рерайт статьи

**POST** `/api/rewrite-article`

Рерайтит статью используя ML или LLM модели.

**Параметры запроса:**
```json
{
    "url": "https://example.com/article",  // Опционально: URL статьи
    "text": "Исходный текст...",          // Опционально: прямой текст
    "style": "scientific|casual|meme",     // Стиль рерайта
    "provider": "rut5|flan|openrouter|yandex"  // Провайдер модели
}
```

**Ответ (успех):**
```json
{
    "success": true,
    "original_text": "Исходный текст...",
    "text": "Переписанный текст...",
    "rewritten_text": "Переписанный текст...",
    "url": "https://example.com/article",
    "style": "scientific",
    "provider": "openrouter",
    "images": {
        "original": "http://localhost:5000/uploads/original.jpg",
        "pexels": null,
        "generated": null
    },
    "url_id": 123
}
```

**Ответ (ошибка):**
```json
{
    "success": false,
    "error": "Описание ошибки"
}
```

**Особенности:**
- Можно указать либо `url`, либо `text`
- Если указан `url`, текст извлекается автоматически
- NLP модели (RUT5, FLAN-T5) работают только с прямым текстом
- LLM модели (Qwen, YandexGPT) могут работать с URL

---

### Сокращение статьи

**POST** `/api/summarize-article`

Сокращает длинную статью до ключевой информации.

**Параметры запроса:**
```json
{
    "url": "https://example.com/article",  // Опционально: URL статьи
    "text": "Длинный текст...",           // Опционально: прямой текст
    "provider": "gazeta|openrouter|yandex"  // Провайдер модели
}
```

**Ответ:**
```json
{
    "success": true,
    "original_text": "Длинный текст...",
    "text": "Сокращенный текст...",
    "url": "https://example.com/article",
    "provider": "gazeta",
    "url_id": 123
}
```

**Особенности:**
- Использует модель Gazeta для русскоязычных текстов
- Может использовать LLM модели для лучшего качества

---

### Отправка статьи в Telegram

**POST** `/api/send-article`

Отправляет обработанную статью в Telegram каналы.

**Параметры запроса:**
```json
{
    "text": "Текст статьи...",
    "channel_ids": ["@channel1", "@channel2"],
    "image_url": "http://example.com/image.jpg"  // Опционально
}
```

**Ответ:**
```json
{
    "success": true,
    "sent_to": ["@channel1", "@channel2"],
    "failed": []
}
```

**Требования:**
- Бот должен быть администратором каналов
- Каналы должны быть добавлены через бота

---

### Получение списка каналов

**GET** `/api/channels`

Возвращает список доступных Telegram каналов.

**Ответ:**
```json
{
    "success": true,
    "channels": [
        {
            "id": "@channel1",
            "name": "Название канала"
        }
    ]
}
```

---

### Аутентификация

#### Генерация токена

**POST** `/api/auth/generate-token`

Генерирует токен авторизации для пользователя.

**Параметры запроса:**
```json
{
    "username": "user123"
}
```

**Ответ:**
```json
{
    "success": true,
    "token": "abc123...",
    "expires_at": "2024-12-31T23:59:59"
}
```

#### Проверка токена

**POST** `/api/auth/verify-token`

Проверяет валидность токена.

**Параметры запроса:**
```json
{
    "token": "abc123..."
}
```

**Ответ:**
```json
{
    "valid": true,
    "username": "user123",
    "expires_at": "2024-12-31T23:59:59"
}
```

#### Авторизация

**POST** `/api/auth/authorize`

Авторизует пользователя по токену.

**Параметры запроса:**
```json
{
    "token": "abc123..."
}
```

**Ответ:**
```json
{
    "success": true,
    "user": {
        "username": "user123",
        "token": "new_token..."
    }
}
```

---

### Работа с пользователями

#### Список всех пользователей

**GET** `/api/users`

Возвращает список всех пользователей.

**Ответ:**
```json
{
    "success": true,
    "users": [
        {
            "id": 1,
            "username": "user1",
            "email": "user1@example.com",
            "created_at": "2024-01-01T00:00:00"
        }
    ]
}
```

#### URL пользователя

**GET** `/api/users/<username>/urls`

Возвращает список URL конкретного пользователя.

**Параметры пути:**
- `username` - имя пользователя

**Ответ:**
```json
{
    "success": true,
    "urls": [
        {
            "id": 1,
            "url": "https://example.com/article",
            "title": "Название статьи",
            "status": "active",
            "created_at": "2024-01-01T00:00:00"
        }
    ]
}
```

#### Статистика пользователя

**GET** `/api/users/<username>/stats`

Возвращает статистику пользователя.

**Ответ:**
```json
{
    "success": true,
    "total_urls": 10,
    "active_urls": 8,
    "total_processed": 25
}
```

---

### Работа с URL

#### Сохранение URL

**POST** `/api/save-url`

Сохраняет URL в базу данных.

**Параметры запроса:**
```json
{
    "url": "https://example.com/article",
    "username": "user123",  // Опционально
    "title": "Название",     // Опционально
    "description": "Описание"  // Опционально
}
```

**Ответ:**
```json
{
    "success": true,
    "url_id": 123
}
```

#### Результаты обработки URL

**GET** `/api/urls/<url_id>/results`

Возвращает результаты обработки конкретного URL.

**Параметры пути:**
- `url_id` - ID URL

**Ответ:**
```json
{
    "success": true,
    "results": [
        {
            "id": 1,
            "original_text": "Исходный текст...",
            "summarized_text": "Сокращенный текст...",
            "paraphrased_text": "Переписанный текст...",
            "processing_time": 5.2,
            "created_at": "2024-01-01T00:00:00"
        }
    ]
}
```

---

### База данных

**GET** `/api/data`

Возвращает данные из базы данных (для отображения в интерфейсе).

**Ответ:**
```json
{
    "success": true,
    "users": [...],
    "urls": [...]
}
```

---

## ML Service API (FastAPI)

Базовый URL: `http://localhost:8000`

Документация API доступна по адресу: `http://localhost:8000/docs`

### Health Check

**GET** `/health`

Проверка работоспособности сервиса.

**Ответ:**
```json
{
    "status": "ok",
    "service": "ml_service"
}
```

---

### Парафразирование

**POST** `/paraphrase`

Парафразирует текст используя локальные ML модели.

**Параметры запроса:**
```json
{
    "text": "Исходный текст для парафразирования",
    "max_length": 512,
    "temperature": 0.7,
    "top_p": 0.9,
    "num_beams": 5
}
```

**Заголовки:**
```
X-API-Key: your-api-key
```

**Ответ:**
```json
{
    "paraphrased": "Переписанный текст...",
    "original": "Исходный текст...",
    "similarity_score": 0.85,
    "processing_time": 2.5,
    "cached": false
}
```

**Особенности:**
- Автоматически определяет язык текста
- Использует соответствующую модель (RUT5 для русского, FLAN-T5 для английского)

---

### Суммаризация

**POST** `/summarize`

Сокращает длинный текст до ключевой информации.

**Параметры запроса:**
```json
{
    "text": "Длинный текст статьи...",
    "target_length": 600,
    "language": "ru"
}
```

**Заголовки:**
```
X-API-Key: your-api-key
```

**Ответ:**
```json
{
    "summary": "Сокращенный текст...",
    "original_length": 2000,
    "summary_length": 580,
    "compression_ratio": 0.29,
    "processing_time": 15.2,
    "cached": false
}
```

**Особенности:**
- Использует модель Gazeta для русского языка
- Автоматически обрезает до полного предложения

---

### Суммаризация по URL

**POST** `/summarize-url`

Извлекает текст по URL и сокращает его.

**Параметры запроса:**
```json
{
    "url": "https://example.com/article",
    "target_length": 600
}
```

**Заголовки:**
```
X-API-Key: your-api-key
```

**Ответ:**
```json
{
    "summary": "Сокращенный текст...",
    "original_length": 2000,
    "summary_length": 580,
    "compression_ratio": 0.29,
    "processing_time": 15.2,
    "cached": false
}
```

---

### Проверка схожести

**POST** `/similarity`

Проверяет семантическую схожесть двух текстов.

**Параметры запроса:**
```json
{
    "text1": "Первый текст...",
    "text2": "Второй текст..."
}
```

**Заголовки:**
```
X-API-Key: your-api-key
```

**Ответ:**
```json
{
    "similarity": 0.85,
    "processing_time": 0.5
}
```

---

### Полная обработка

**POST** `/process`

Полная обработка текста (извлечение, суммаризация, парафразирование).

**Параметры запроса:**
```json
{
    "url": "https://example.com/article",
    "summarize": true,
    "paraphrase": true
}
```

**Заголовки:**
```
X-API-Key: your-api-key
```

**Ответ:**
```json
{
    "original_text": "Исходный текст...",
    "summarized": "Сокращенный текст...",
    "paraphrased": "Переписанный текст...",
    "processing_time": 20.5
}
```

---

## Внешние API зависимости

### OpenRouter API

**Назначение:** Доступ к LLM моделям (Qwen 2.5 72B)

**URL:** `https://openrouter.ai/api/v1/chat/completions`

**Аутентификация:**
```
Authorization: Bearer <OPENROUTER_API_KEY>
```

**Использование:**
- Рерайт текстов через Qwen
- Гибкая настройка стиля

**Документация:** https://openrouter.ai/docs

---

### Yandex Cloud API

**Назначение:** Доступ к YandexGPT

**URL:** `https://rest-assistant.api.cloud.yandex.net/v1`

**Аутентификация:**
```
Authorization: Bearer <YANDEX_CLOUD_API_KEY>
x-folder-id: <YANDEX_CLOUD_PROJECT>
```

**Использование:**
- Рерайт текстов через YandexGPT
- Оптимизация для русского языка

**Документация:** https://cloud.yandex.ru/docs/yandexgpt/

---

### Telegram Bot API

**Назначение:** Управление каналами и отправка сообщений

**URL:** `https://api.telegram.org/bot<BOT_TOKEN>/`

**Аутентификация:**
```
BOT_TOKEN в .env файле
```

**Использование:**
- Отправка статей в каналы
- Управление списком каналов
- Авторизация пользователей

**Документация:** https://core.telegram.org/bots/api

**Библиотека:** aiogram 3.x (Python)

---

### Kandinsky API (FusionBrain)

**Назначение:** Генерация изображений

**URL:** Зависит от метода (API или Web)

**Аутентификация:**
```
FUSIONBRAIN_API_KEY
FUSIONBRAIN_SECRET_KEY
```

**Использование:**
- Генерация изображений для статей
- Альтернатива поиску изображений

**Документация:** https://fusionbrain.ai/

---

### Pexels API

**Назначение:** Поиск изображений для статей

**URL:** `https://api.pexels.com/v1/`

**Аутентификация:**
```
Authorization: <PEXELS_API_KEY>
```

**Использование:**
- Поиск релевантных изображений
- Извлечение изображений из статей

**Документация:** https://www.pexels.com/api/

---

### Unsplash API

**Назначение:** Альтернативный поиск изображений

**URL:** `https://api.unsplash.com/`

**Аутентификация:**
```
Authorization: Client-ID <UNSPLASH_API_KEY>
```

**Использование:**
- Резервный источник изображений
- Высокое качество фотографий

**Документация:** https://unsplash.com/documentation

---

## Аутентификация

### API Key для ML Service

Все запросы к ML Service требуют заголовок:

```
X-API-Key: your-api-key
```

**Настройка:**
```bash
API_KEY=your-api-key-here
```

### Токены для Rewrite Service

Rewrite Service использует токены для авторизации пользователей:

1. Генерация токена через `/api/auth/generate-token`
2. Проверка через `/api/auth/verify-token`
3. Авторизация через `/api/auth/authorize`

**Особенности:**
- Токены имеют срок действия (по умолчанию 10 лет)
- Токены хранятся в `auth_tokens.json`

---

## Примеры использования

### Рерайт через Rewrite Service

```python
import requests

response = requests.post(
    "http://localhost:5000/api/rewrite-article",
    json={
        "text": "Исходный текст...",
        "style": "scientific",
        "provider": "openrouter"
    }
)

result = response.json()
print(result["text"])
```

### Парафразирование через ML Service

```python
import requests

response = requests.post(
    "http://localhost:8000/paraphrase",
    json={
        "text": "Исходный текст...",
        "max_length": 512,
        "temperature": 0.7
    },
    headers={
        "X-API-Key": "your-api-key"
    }
)

result = response.json()
print(result["paraphrased"])
```

### Суммаризация через ML Service

```python
import requests

response = requests.post(
    "http://localhost:8000/summarize",
    json={
        "text": "Длинный текст...",
        "target_length": 600,
        "language": "ru"
    },
    headers={
        "X-API-Key": "your-api-key"
    }
)

result = response.json()
print(result["summary"])
```

---

## Ограничения и рекомендации

### Rate Limits

- **ML Service**: Нет жестких ограничений, но рекомендуется не более 10 запросов в секунду
- **OpenRouter**: Зависит от тарифа (см. документацию OpenRouter)
- **YandexGPT**: Зависит от тарифа (см. документацию Yandex Cloud)
- **Telegram Bot**: 30 сообщений в секунду

### Таймауты

- **ML Service**: 300 секунд для обработки текста
- **Rewrite Service**: 120 секунд для рерайта
- **OpenRouter**: 60 секунд
- **YandexGPT**: 60 секунд

### Рекомендации

1. Используйте кэширование для повторяющихся запросов
2. Обрабатывайте длинные тексты частями
3. Используйте асинхронные запросы для параллельной обработки
4. Проверяйте статус сервисов через health check эндпоинты

---

## Заключение

API Phoenix LAB предоставляет полный набор эндпоинтов для работы с текстами, пользователями и интеграцией с внешними сервисами. Все эндпоинты документированы и доступны через Swagger UI для ML Service (`/docs`).
