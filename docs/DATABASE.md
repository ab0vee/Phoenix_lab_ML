# База данных - Подробная документация

## Содержание

1. [Обзор](#обзор)
2. [Схема базы данных](#схема-базы-данных)
3. [Модели данных](#модели-данных)
4. [API эндпоинты для БД](#api-эндпоинты-для-бд)
5. [Работа с пользователями](#работа-с-пользователями)
6. [Работа со ссылками](#работа-со-ссылками)
7. [Результаты обработки](#результаты-обработки)

---

## Обзор

База данных Phoenix LAB использует **PostgreSQL** для хранения пользователей, их URL и результатов обработки текстов. Система использует SQLAlchemy ORM для работы с БД.

**Технологии:**
- PostgreSQL 15
- SQLAlchemy ORM
- Python 3.10+

---

## Схема базы данных

### Таблицы

1. **users** - Пользователи системы
2. **user_urls** - URL пользователей
3. **url_processing_results** - Результаты обработки URL
4. **user_sessions** - Сессии пользователей

### Связи

```
users (1) ────< (N) user_urls
users (1) ────< (N) user_sessions
user_urls (1) ────< (N) url_processing_results
```

---

## Модели данных

### User (Пользователь)

**Таблица:** `users`

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор
- `username` (String(100), Unique, Indexed) - Имя пользователя
- `email` (String(255), Unique, Nullable, Indexed) - Email пользователя
- `password_hash` (String(255)) - Хэш пароля (для будущего использования)
- `full_name` (String(255), Nullable) - Полное имя
- `is_active` (Boolean, Default: True) - Активен ли пользователь
- `is_admin` (Boolean, Default: False) - Администратор ли
- `created_at` (DateTime, Default: utcnow) - Дата создания
- `updated_at` (DateTime, Default: utcnow, OnUpdate: utcnow) - Дата обновления
- `last_login` (DateTime, Nullable) - Последний вход

**Связи:**
- `urls` - Список URL пользователя (One-to-Many)
- `sessions` - Сессии пользователя (One-to-Many)

**Пример:**
```python
{
    "id": 1,
    "username": "telegram_123456",
    "email": None,
    "is_active": True,
    "is_admin": False,
    "created_at": "2024-01-01T00:00:00"
}
```

### UserUrl (URL пользователя)

**Таблица:** `user_urls`

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор
- `user_id` (Integer, FK → users.id, Indexed) - ID пользователя
- `url` (Text) - URL статьи
- `title` (String(500), Nullable) - Название статьи
- `description` (Text, Nullable) - Описание
- `status` (String(50), Default: 'active', Indexed) - Статус URL
- `created_at` (DateTime, Default: utcnow, Indexed) - Дата создания
- `updated_at` (DateTime, Default: utcnow, OnUpdate: utcnow) - Дата обновления
- `last_processed_at` (DateTime, Nullable) - Последняя обработка
- `metadata` (JSON, Nullable) - Дополнительные данные

**Связи:**
- `user` - Пользователь (Many-to-One)
- `processing_results` - Результаты обработки (One-to-Many)

**Статусы:**
- `active` - Активный URL
- `archived` - Архивированный
- `deleted` - Удаленный

**Пример:**
```python
{
    "id": 1,
    "user_id": 1,
    "url": "https://example.com/article",
    "title": "Название статьи",
    "status": "active",
    "created_at": "2024-01-01T00:00:00",
    "last_processed_at": "2024-01-02T00:00:00"
}
```

### UrlProcessingResult (Результат обработки)

**Таблица:** `url_processing_results`

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор
- `url_id` (Integer, FK → user_urls.id, Indexed) - ID URL
- `original_text` (Text, Nullable) - Оригинальный текст
- `summarized_text` (Text, Nullable) - Сокращенный текст
- `paraphrased_text` (Text, Nullable) - Переписанный текст
- `language` (String(10), Nullable) - Язык текста
- `processing_time` (Integer, Nullable) - Время обработки (секунды)
- `created_at` (DateTime, Default: utcnow, Indexed) - Дата создания
- `metadata` (JSON, Nullable) - Дополнительные данные

**Связи:**
- `url` - URL (Many-to-One)

**Пример:**
```python
{
    "id": 1,
    "url_id": 1,
    "original_text": "Исходный текст...",
    "summarized_text": "Сокращенный текст...",
    "paraphrased_text": "Переписанный текст...",
    "language": "ru",
    "processing_time": 5,
    "created_at": "2024-01-02T00:00:00"
}
```

### UserSession (Сессия пользователя)

**Таблица:** `user_sessions`

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор
- `user_id` (Integer, FK → users.id, Indexed) - ID пользователя
- `session_token` (String(255), Unique, Indexed) - Токен сессии
- `expires_at` (DateTime, Indexed) - Срок действия
- `created_at` (DateTime, Default: utcnow) - Дата создания
- `ip_address` (String(45), Nullable) - IP адрес
- `user_agent` (Text, Nullable) - User Agent

**Связи:**
- `user` - Пользователь (Many-to-One)

---

## API эндпоинты для БД

### Получение всех пользователей

**GET** `/api/users`

Возвращает список всех пользователей системы.

**Ответ:**
```json
{
    "success": true,
    "users": [
        {
            "id": 1,
            "username": "telegram_123456",
            "email": null,
            "is_active": true,
            "created_at": "2024-01-01T00:00:00"
        }
    ],
    "total": 1
}
```

**Использование:**
- Административная панель
- Мониторинг пользователей

---

### Получение URL пользователя

**GET** `/api/users/<username>/urls`

Возвращает все URL конкретного пользователя.

**Параметры пути:**
- `username` - имя пользователя

**Ответ:**
```json
{
    "success": true,
    "user_id": 1,
    "username": "telegram_123456",
    "urls": [
        {
            "id": 1,
            "url": "https://example.com/article",
            "title": "Название статьи",
            "status": "active",
            "created_at": "2024-01-01T00:00:00",
            "last_processed_at": "2024-01-02T00:00:00"
        }
    ],
    "total": 1
}
```

**Использование:**
- Отображение URL пользователя в интерфейсе
- История обработанных статей

---

### Статистика пользователя

**GET** `/api/users/<username>/stats`

Возвращает статистику пользователя.

**Параметры пути:**
- `username` - имя пользователя

**Ответ:**
```json
{
    "success": true,
    "user_id": 1,
    "username": "telegram_123456",
    "stats": {
        "total_urls": 10,
        "active_urls": 8,
        "archived_urls": 2,
        "total_processed": 25,
        "last_processed_at": "2024-01-02T00:00:00"
    }
}
```

**Использование:**
- Отображение статистики в профиле
- Аналитика использования

---

### Результаты обработки URL

**GET** `/api/urls/<url_id>/results`

Возвращает результаты обработки конкретного URL.

**Параметры пути:**
- `url_id` - ID URL

**Ответ:**
```json
{
    "success": true,
    "url_id": 1,
    "url": "https://example.com/article",
    "results": [
        {
            "id": 1,
            "original_text": "Исходный текст...",
            "paraphrased_text": "Переписанный текст...",
            "summarized_text": "Сокращенный текст...",
            "language": "ru",
            "processing_time": 5,
            "created_at": "2024-01-02T00:00:00"
        }
    ],
    "total": 1
}
```

**Использование:**
- История обработки конкретного URL
- Просмотр предыдущих результатов

---

### Сохранение URL

**POST** `/api/save-url`

Сохраняет URL в базу данных без обработки.

**Параметры запроса:**
```json
{
    "url": "https://example.com/article",
    "username": "telegram_123456",  // Опционально
    "title": "Название",            // Опционально
    "description": "Описание"       // Опционально
}
```

**Ответ:**
```json
{
    "success": true,
    "url_id": 1,
    "message": "URL успешно сохранен"
}
```

**Использование:**
- Сохранение URL для последующей обработки
- Создание списка избранных статей

---

### Все данные (для интерфейса)

**GET** `/api/data`

Возвращает все данные в табличном формате для отображения в интерфейсе.

**Ответ:**
```json
{
    "success": true,
    "users": [...],
    "urls": [...]
}
```

**Использование:**
- Отображение данных в интерфейсе Database Menu
- Экспорт данных

---

## Работа с пользователями

### Создание пользователя

Пользователи создаются автоматически при:
1. Авторизации через Telegram бота
2. Сохранении первого URL
3. Вызове функции `get_or_create_user()`

**Функция:**
```python
from database import get_or_create_user

user = get_or_create_user(
    username="telegram_123456",
    email=None
)
```

**Процесс:**
1. Проверка существования пользователя по username
2. Если не существует - создание нового
3. Возврат пользователя

### Получение пользователя

```python
from database import get_or_create_user

user = get_or_create_user(username="telegram_123456")
```

### Автоматическое создание при авторизации

При авторизации через Telegram бота:

```python
# В /api/auth/authorize
from database import get_or_create_user

username = user_data.get('username') or f"telegram_{user_data.get('id')}"
user = get_or_create_user(username=username, email=None)
```

---

## Работа со ссылками

### Сохранение URL

**Через API:**
```python
POST /api/save-url
{
    "url": "https://example.com/article",
    "username": "telegram_123456"
}
```

**Через функцию:**
```python
from database import save_user_url, get_or_create_user

user = get_or_create_user(username="telegram_123456")
url = save_user_url(
    user_id=user.id,
    url="https://example.com/article",
    title="Название статьи"
)
```

### Получение URL пользователя

```python
from database import get_user_urls

urls = get_user_urls(user_id=1)
```

### Обновление статуса URL

```python
from database import get_db_session
from models import UserUrl

session = get_db_session()
url = session.query(UserUrl).filter_by(id=1).first()
url.status = "archived"
url.last_processed_at = datetime.utcnow()
session.commit()
session.close()
```

### Автоматическое сохранение при обработке

При обработке статьи через `/api/rewrite-article` или `/api/summarize-article`:

1. Извлекается username из токена или запроса
2. Создается/находится пользователь
3. Сохраняется URL (если был передан URL)
4. Сохраняются результаты обработки

**Пример:**
```python
# В rewrite_article()
if article_url:
    user = get_or_create_user(username=username)
    url = save_user_url(
        user_id=user.id,
        url=article_url,
        title=extracted_title
    )
    url_id = url.id
```

---

## Результаты обработки

### Сохранение результатов

**Автоматически при обработке:**
```python
from database import save_processing_result

result = save_processing_result(
    url_id=1,
    original_text="Исходный текст...",
    paraphrased_text="Переписанный текст...",
    summarized_text="Сокращенный текст...",
    language="ru",
    processing_time=5
)
```

**При рерайте через API:**
- URL автоматически сохраняется
- Результаты обработки сохраняются в `url_processing_results`

### Получение результатов

**Через API:**
```
GET /api/urls/<url_id>/results
```

**Через функцию:**
```python
from database import get_processing_results

results = get_processing_results(url_id=1, limit=10)
```

**Параметры:**
- `url_id` - ID URL
- `limit` - Максимальное количество результатов (по умолчанию 10)

### Статистика обработки

```python
from database import get_user_stats

stats = get_user_stats(user_id=1)
# Возвращает:
# - total_urls
# - active_urls
# - archived_urls
# - total_processed
# - last_processed_at
```

---

## Примеры использования

### Полный цикл работы с БД

```python
# 1. Создание/получение пользователя
from database import get_or_create_user

user = get_or_create_user(username="telegram_123456")

# 2. Сохранение URL
from database import save_user_url

url = save_user_url(
    user_id=user.id,
    url="https://example.com/article",
    title="Название статьи"
)

# 3. Обработка статьи (через API или напрямую)
# ... обработка текста ...

# 4. Сохранение результатов
from database import save_processing_result

result = save_processing_result(
    url_id=url.id,
    original_text="Исходный текст...",
    paraphrased_text="Переписанный текст...",
    language="ru",
    processing_time=5
)

# 5. Получение результатов
from database import get_processing_results

results = get_processing_results(url_id=url.id)
```

### Получение статистики через API

```python
import requests

# Получение всех пользователей
response = requests.get("http://localhost:5000/api/users")
users = response.json()["users"]

# Получение URL пользователя
response = requests.get(f"http://localhost:5000/api/users/{users[0]['username']}/urls")
urls = response.json()["urls"]

# Получение статистики
response = requests.get(f"http://localhost:5000/api/users/{users[0]['username']}/stats")
stats = response.json()["stats"]

# Получение результатов обработки
response = requests.get(f"http://localhost:5000/api/urls/{urls[0]['id']}/results")
results = response.json()["results"]
```

---

## Особенности реализации

### Опциональная БД

База данных является **опциональной**. Система может работать без БД:

- Если БД недоступна, все эндпоинты возвращают ошибку 503
- Функции обработки текста работают без БД
- Сохранение URL и результатов не выполняется

**Проверка доступности:**
```python
DB_AVAILABLE = check_database_connection()
```

### Автоматическое создание пользователей

Пользователи создаются автоматически при:
- Авторизации через бота
- Первом сохранении URL
- Любом обращении к функциям работы с пользователями

### Формат username

Для Telegram пользователей используется формат:
- `telegram_<user_id>` - если username не указан
- `<username>` - если username указан

---

## Заключение

База данных Phoenix LAB предоставляет полный функционал для хранения пользователей, их URL и результатов обработки. Все операции доступны через API эндпоинты, что позволяет легко интегрировать с фронтендом и другими сервисами.

