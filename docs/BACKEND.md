# Backend - Подробная документация

## Содержание

1. [Обзор](#обзор)
2. [Архитектура бэкенда](#архитектура-бэкенда)
3. [Rewrite Service (Flask)](#rewrite-service-flask)
4. [ML Service (FastAPI)](#ml-service-fastapi)
5. [База данных](#база-данных)
6. [Интеграции](#интеграции)

---

## Обзор

Бэкенд Phoenix LAB состоит из нескольких микросервисов:

1. **Rewrite Service (Flask)** - основной API сервис
2. **ML Service (FastAPI)** - сервис обработки текста
3. **Telegram Bot (aiogram)** - бот для управления каналами
4. **PostgreSQL** - база данных
5. **Redis** - кэширование

Все сервисы независимы, но взаимодействуют через API и общую сеть Docker.

---

## Архитектура бэкенда

### Микросервисная архитектура

```
┌─────────────────────────────────────┐
│      Frontend (Next.js)             │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┬──────────────┐
       │                │              │
┌──────▼──────┐  ┌──────▼──────┐  ┌───▼──────┐
│   Rewrite   │  │     ML      │  │ Telegram │
│   Service   │  │   Service   │  │   Bot    │
│  (Flask)    │  │  (FastAPI)  │  │(aiogram) │
└──────┬──────┘  └──────┬──────┘  └─────┬────┘
       │                │                │
       └────────────────┴────────────────┘
                │               │
        ┌───────┴───────┐  ┌───▼──────┐
        │  PostgreSQL   │  │  Redis   │
        └───────────────┘  └──────────┘
```

### Преимущества микросервисов

- ✅ **Независимость** - каждый сервис можно обновлять отдельно
- ✅ **Масштабируемость** - можно масштабировать каждый сервис отдельно
- ✅ **Технологическая гибкость** - разные технологии для разных задач
- ✅ **Отказоустойчивость** - падение одного сервиса не останавливает другие

---

## Rewrite Service (Flask)

### Назначение

Основной API сервис для:
- Рерайта статей через LLM провайдеры
- Суммаризации статей
- Управления пользователями и URL
- Интеграции с внешними API
- Отправки статей в Telegram

### Технологии

- **Flask** - веб-фреймворк
- **Python 3.10+**
- **SQLAlchemy** - ORM для работы с БД
- **aiogram** - для отправки в Telegram
- **requests** - для HTTP запросов

### Структура

```
backend/rewrite_service/
├── server.py          # Главный файл сервиса
├── database.py        # Функции работы с БД
├── requirements.txt   # Зависимости
└── Dockerfile        # Docker конфигурация
```

### Основные функции

#### Рерайт статьи

```python
@app.route('/api/rewrite-article', methods=['POST'])
def rewrite_article():
    # Извлечение текста (URL или прямой текст)
    # Выбор провайдера (RUT5, FLAN-T5, Qwen, YandexGPT)
    # Обработка текста
    # Возврат результата
```

**Провайдеры:**
- `rut5` - ML модель RUT5 (через ML Service)
- `flan` - ML модель FLAN-T5 (через ML Service)
- `openrouter` - LLM Qwen (через OpenRouter API)
- `yandex` - LLM YandexGPT (через Yandex Cloud API)

#### Суммаризация

```python
@app.route('/api/summarize-article', methods=['POST'])
def summarize_article():
    # Извлечение текста
    # Выбор провайдера (Gazeta, Qwen, YandexGPT)
    # Суммаризация
    # Возврат результата
```

#### Работа с БД

```python
# Сохранение URL
save_user_url(user_id, url, title)

# Получение URL пользователя
get_user_urls(user_id)

# Сохранение результатов обработки
save_processing_result(url_id, original_text, paraphrased_text)
```

### Интеграция с ML Service

**Запросы к ML Service:**
```python
response = requests.post(
    f"{ML_SERVICE_URL}/paraphrase",
    json={"text": text, "max_length": 512},
    headers={"X-API-Key": API_KEY},
    timeout=300
)
```

### Интеграция с LLM провайдерами

#### OpenRouter

```python
def rewrite_article_with_openrouter(article_text, style):
    response = requests.post(
        OPENROUTER_API_URL,
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        json={
            "model": OPENROUTER_MODEL,
            "messages": [...]
        }
    )
```

#### YandexGPT

```python
def rewrite_article_with_yandex(article_text, style):
    response = yandex_client.responses.create(
        prompt={"id": YANDEX_CLOUD_ASSISTANT_ID},
        input=full_prompt
    )
```

### Извлечение текста из URL

```python
def extract_article_text(url):
    # Загрузка HTML
    # Парсинг с BeautifulSoup
    # Извлечение основного контента
    # Очистка от рекламы и лишних элементов
    # Возврат текста
```

---

## ML Service (FastAPI)

### Назначение

Сервис для обработки текста локальными ML моделями:
- Парафразирование текста
- Суммаризация текста
- Проверка схожести текстов

### Технологии

- **FastAPI** - веб-фреймворк
- **Python 3.10+**
- **Hugging Face Transformers** - библиотека для ML моделей
- **PyTorch** - фреймворк для ML
- **sentence-transformers** - для проверки схожести

### Структура

```
backend/ml_service/
├── main.py              # Главный файл FastAPI
├── config.py            # Конфигурация
├── api/
│   ├── routes/          # API эндпоинты
│   ├── schemas.py       # Pydantic схемы
│   └── dependencies.py  # Зависимости (API Key)
├── services/
│   ├── text_processor.py    # Обработка текста
│   ├── model_manager.py     # Управление моделями
│   └── content_extractor.py # Извлечение контента
└── Dockerfile
```

### Основные эндпоинты

#### Парафразирование

```python
@router.post("/paraphrase")
async def paraphrase_text(request: ParaphraseRequest):
    paraphrased = await text_processor.paraphrase(
        text=request.text,
        max_length=request.max_length,
        temperature=request.temperature
    )
    return ParaphraseResponse(paraphrased=paraphrased)
```

#### Суммаризация

```python
@router.post("/summarize")
async def summarize_text(request: SummarizeRequest):
    summary = await text_processor.summarize(
        text=request.text,
        target_length=request.target_length,
        language=request.language
    )
    return SummarizeResponse(summary=summary)
```

### Управление моделями

**Lazy Loading:**
- Модели загружаются при первом запросе
- Кэшируются в памяти
- Не загружаются при старте (если `PRELOAD_MODELS=false`)

**Preload:**
- Модели загружаются при старте сервиса
- Готовы к работе сразу
- Медленный старт, но быстрые первые запросы

### Оптимизация

**Память:**
- Float16 на CUDA для экономии памяти
- Очистка кэша после загрузки
- Оптимизация через `torch.no_grad()`

**Производительность:**
- Асинхронная обработка
- Кэширование результатов
- Оптимизация параметров генерации

---

## База данных

### PostgreSQL

**Назначение:**
- Хранение пользователей
- Хранение URL пользователей
- Хранение результатов обработки
- Хранение сессий

**Подключение:**
```python
DATABASE_URL = "postgresql://user:password@postgres:5432/phoenix_lab"
```

**Модели:**
- `User` - пользователи
- `UserUrl` - URL пользователей
- `UrlProcessingResult` - результаты обработки
- `UserSession` - сессии

### SQLAlchemy ORM

**Использование:**
```python
from database import get_or_create_user, save_user_url

user = get_or_create_user(username="telegram_123456")
url = save_user_url(user_id=user.id, url="https://example.com/article")
```

**Преимущества:**
- Типобезопасность
- Автоматическая миграция схем
- Удобная работа с данными

---

## Интеграции

### Внешние API

#### OpenRouter

**Назначение:** Доступ к LLM моделям (Qwen)

**Интеграция:**
```python
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
response = requests.post(
    'https://openrouter.ai/api/v1/chat/completions',
    headers={'Authorization': f'Bearer {OPENROUTER_API_KEY}'},
    json={...}
)
```

#### Yandex Cloud

**Назначение:** Доступ к YandexGPT

**Интеграция:**
```python
from openai import OpenAI

yandex_client = OpenAI(
    api_key=YANDEX_CLOUD_API_KEY,
    base_url="https://rest-assistant.api.cloud.yandex.net/v1"
)
```

#### Telegram Bot API

**Назначение:** Отправка сообщений в каналы

**Интеграция:**
```python
from aiogram import Bot

bot = Bot(token=BOT_TOKEN)
await bot.send_message(channel_id, text)
```

### Внутренние сервисы

#### ML Service

**Запросы:**
```python
response = requests.post(
    f"{ML_SERVICE_URL}/paraphrase",
    json={"text": text},
    headers={"X-API-Key": API_KEY},
    timeout=300
)
```

#### PostgreSQL

**Подключение:**
```python
from sqlalchemy import create_engine
engine = create_engine(DATABASE_URL)
```

#### Redis

**Использование (для будущего):**
```python
import redis
r = redis.Redis(host='redis', port=6379)
r.set('key', 'value')
```

---

## Обработка ошибок

### Типы ошибок

1. **Ошибки API запросов**
   - Таймауты
   - Неверные ответы
   - Сетевые ошибки

2. **Ошибки БД**
   - Проблемы подключения
   - Ошибки запросов
   - Ошибки валидации

3. **Ошибки обработки**
   - Ошибки моделей
   - Ошибки парсинга
   - Ошибки валидации данных

### Логирование

**Использование:**
```python
import logging

logger = logging.getLogger(__name__)
logger.info("Информационное сообщение")
logger.error("Ошибка: %s", error_message)
```

**Уровни:**
- `INFO` - обычные операции
- `WARNING` - предупреждения
- `ERROR` - ошибки
- `DEBUG` - отладочная информация

---

## Безопасность

### API Key

**Защита ML Service:**
```python
def verify_api_key(api_key: str = Header(...)):
    if api_key != settings.api_key:
        raise HTTPException(401, "Invalid API Key")
    return api_key
```

### Валидация данных

**Pydantic схемы:**
```python
class ParaphraseRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    max_length: int = Field(512, ge=1, le=2048)
```

### CORS

**Настройка:**
```python
from flask_cors import CORS
CORS(app)  # Разрешает запросы с фронтенда
```

---

## Производительность

### Кэширование

**Результаты обработки:**
- Кэширование в Redis (для будущего)
- Кэширование моделей в памяти

### Асинхронность

**FastAPI:**
- Async/await для обработки запросов
- Параллельная обработка

**aiogram:**
- Асинхронные запросы к Telegram API
- Эффективная обработка множества запросов

### Оптимизация запросов

**БД:**
- Индексы на часто используемых полях
- Оптимизация SQL запросов

**ML:**
- Lazy loading моделей
- Оптимизация параметров генерации
- Использование GPU (если доступно)

---

## Заключение

Бэкенд Phoenix LAB построен на микросервисной архитектуре, что обеспечивает масштабируемость, независимость сервисов и гибкость разработки. Каждый сервис решает свою задачу наиболее подходящими технологиями:

- **Flask** для простого и гибкого API
- **FastAPI** для высокопроизводительного ML сервиса
- **aiogram** для эффективного Telegram бота
- **PostgreSQL** для надежного хранения данных

Все сервисы интегрированы через API и общую сеть Docker, что упрощает развертывание и масштабирование.

