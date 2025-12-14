# Phoenix LAB - Система автоматической публикации новостей

## 📋 Оглавление

- [Описание проекта](#описание-проекта)
- [Основные возможности](#основные-возможности)
- [Архитектура системы](#архитектура-системы)
- [Технологический стек](#технологический-стек)
- [Быстрый старт](#быстрый-старт)
- [Документация](#документация)
- [Структура проекта](#структура-проекта)

## 🎯 Описание проекта

Phoenix LAB — это комплексная система для автоматической обработки и публикации новостного контента в различных мессенджер-платформах и социальных сетях. Система использует машинное обучение для парафразирования текстов без потери контекста и смысла, что позволяет публиковать один и тот же контент на разных платформах, избегая дублирования.

### Ключевые особенности

- 📰 **Автоматическое извлечение** текста по ссылке или из сообщения
- ✂️ **Выжимка/суммаризация** длинных материалов без потери контекста
- 🤖 **Автоматическое парафразирование** новостных текстов с сохранением смысла
- 📱 **Мультиплатформенная публикация** в Telegram, VK, Instagram
- 🎛️ **Веб-панель управления** для настройки и мониторинга
- 🔄 **Управление Telegram-ботом** через веб-интерфейс
- 📊 **Аналитика и логирование** всех операций
- ⚡ **Высокая производительность** благодаря кэшированию и асинхронной обработке

## 🚀 Быстрый запуск

### Автоматический запуск всех сервисов

Запустите в корне проекта:
```bash
start_all.bat
```

Это запустит:
- **Frontend** (Next.js) - http://localhost:3000
- **Rewrite Service** (Flask) - http://localhost:5000
- **Telegram Bot** - ожидает команды
- **ML Service** - инструкция по запуску через Docker

Для остановки:
```bash
stop_all.bat
```

📖 **Подробная инструкция:** см. [START_PROJECT.md](START_PROJECT.md)

---

## 🚀 Основные возможности

### 1. Обработка новостей
- Загрузка новостных текстов через веб-интерфейс или API
- Автоматическое парафразирование с использованием ML-модели
- Проверка семантической схожести оригинального и обработанного текста
- Сохранение истории изменений

### 2. Публикация контента
- **Telegram**: автоматическая публикация в каналы и группы через бота
- **VK**: публикация на стене группы/страницы
- **Instagram**: публикация постов (требуется бизнес-аккаунт)
- Планирование публикаций на определенное время
- Массовая публикация с настраиваемыми задержками

### 3. Управление ботом
- Настройка команд и ответов бота
- Управление подписками и каналами
- Мониторинг активности бота
- Статистика использования

### 4. Аналитика
- Отслеживание успешности публикаций
- Статистика по платформам
- Логирование ошибок и предупреждений
- Экспорт данных

## 🏗️ Архитектура системы

Система построена по микросервисной архитектуре с разделением на следующие компоненты:

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js Web Application                   │
│              (Admin Panel + Telegram WebApp)                │
└──────────────┬───────────────────────────────────────────────┘
               │
       ┌───────┴────────┬──────────────┬──────────────┐
       │                │              │              │
┌──────▼──────┐  ┌──────▼──────┐  ┌───▼──────┐  ┌───▼──────┐
│  Telegram   │  │   ML        │  │ Publisher│  │ Database │
│    Bot      │  │  Service    │  │ Service  │  │          │
│ (aiogram)   │  │ (FastAPI)   │  │          │  │(PostgreSQL)
└──────┬──────┘  └──────┬──────┘  └─────┬────┘  └─────┬────┘
       │                │                │             │
       │                │                │             │
┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐     │
│  Telegram   │  │  Hugging    │  │   Redis     │     │
│    API      │  │   Face      │  │  (Cache +   │     │
│             │  │  Models     │  │   Queue)    │     │
└─────────────┘  └─────────────┘  └─────────────┘     │
                                                       │
                                              ┌────────▼────────┐
                                              │  External APIs  │
                                              │  VK, Instagram  │
                                              └─────────────────┘
```

Подробное описание архитектуры см. в [ARCHITECTURE.md](./docs/ARCHITECTURE.md).

## 🛠️ Технологический стек

### Frontend
- **Next.js 14+** (App Router) - React-фреймворк с SSR
- **TypeScript** - типизированный JavaScript
- **Tailwind CSS** - utility-first CSS фреймворк
- **shadcn/ui** - компоненты UI
- **@telegram-apps/sdk** - официальный SDK для Telegram WebApp

### Backend
- **FastAPI** (Python) - высокопроизводительный веб-фреймворк для ML-сервиса
- **aiogram 3.x** (Python) - асинхронный фреймворк для Telegram бота
- **PostgreSQL** - реляционная база данных
- **Redis** - кэширование и очереди задач
- **Celery** - распределенная очередь задач

### Machine Learning
- **Hugging Face Transformers** - библиотека для работы с моделями
- **google/flan-t5-large** - модель для парафразирования (или альтернативы)
- **LoRA/QLoRA** - эффективное fine-tuning
- **sentence-transformers** - проверка семантической схожести
- **Accelerate** - оптимизация обучения
- **PEFT** - параметр-эффективные методы fine-tuning

### Интеграции
- **python-telegram-bot / aiogram** - Telegram API
- **vk-api** (Python) - VK API
- **instagrapi** или **Instagram Graph API** - Instagram API

### DevOps
- **Docker** + **Docker Compose** - контейнеризация
- **GitHub Actions** - CI/CD
- **Nginx** - reverse proxy (опционально)

## 🚀 Быстрый старт

### Вариант 1: Запуск через Docker (рекомендуется)

**Требования:**
- Docker Desktop (Windows/Mac) или Docker Engine (Linux)
- Минимум 8GB RAM (рекомендуется 16GB)

**Запуск:**
```bash
# Windows
docker-start.bat

# PowerShell
.\docker-start.ps1

# Linux/Mac
docker-compose up -d --build
```

📖 **Подробная инструкция:** см. [DOCKER.md](DOCKER.md)

### Вариант 2: Запуск без Docker

**Требования:**
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ (опционально)
- Redis 7+ (опционально)

**Запуск:**
```bash
# Автоматический запуск всех сервисов
start_all.bat

# Или вручную:
# Frontend
cd frontend && npm run dev

# Rewrite Service
cd backend/rewrite_service && python server.py

# Telegram Bot
cd backend/telegram_bot && python main.py

# ML Service (через Docker)
cd backend/ml_service && docker-compose up -d
```

📖 **Подробная инструкция:** см. [START_PROJECT.md](START_PROJECT.md)

## 📚 Документация

- [ARCHITECTURE.md](./docs/ARCHITECTURE.md) - Детальная архитектура системы
- [SETUP.md](./docs/SETUP.md) - Инструкции по установке и настройке
- [ML_MODEL.md](./docs/ML_MODEL.md) - Документация по ML-модели и обучению
- [API.md](./docs/API.md) - API документация
- [DEPLOYMENT.md](./docs/DEPLOYMENT.md) - Инструкции по развертыванию
- [PLATFORMS.md](./docs/PLATFORMS.md) - Руководство по публикации на платформах
- [FRONTEND_SPEC.md](./docs/FRONTEND_SPEC.md) - ТЗ на фронтенд (отдельно от бэкенда)

## 📁 Структура проекта

```
phoenix-lab/
├── frontend/                 # Next.js приложение
│   ├── app/                  # App Router страницы
│   ├── components/           # React компоненты
│   ├── lib/                  # Утилиты и конфигурация
│   └── public/               # Статические файлы
│
├── backend/                  # Backend сервисы
│   ├── ml_service/           # FastAPI ML-сервис
│   │   ├── api/              # API endpoints
│   │   ├── models/           # ML модели и логика
│   │   └── utils/            # Утилиты
│   │
│   ├── telegram_bot/         # Telegram бот (aiogram)
│   │   ├── handlers/         # Обработчики команд
│   │   ├── keyboards/        # Клавиатуры
│   │   └── middleware/       # Middleware
│   │
│   └── publisher_service/    # Сервис публикаций
│       ├── adapters/         # Адаптеры для платформ
│       └── schedulers/       # Планировщики
│
├── shared/                   # Общий код
│   └── schemas/              # Pydantic схемы
│
├── database/                 # Миграции и схемы БД
│   └── migrations/
│
├── docker/                    # Docker конфигурации
│   ├── Dockerfile.ml-service
│   ├── Dockerfile.telegram-bot
│   └── docker-compose.yml
│
├── docs/                     # Документация
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   ├── ML_MODEL.md
│   ├── API.md
│   └── DEPLOYMENT.md
│
├── scripts/                  # Вспомогательные скрипты
│   ├── setup.sh
│   └── train_model.py
│
└── tests/                    # Тесты
    ├── unit/
    └── integration/
```

## 🔧 Конфигурация

Основные настройки находятся в файлах:

- `backend/.env` - переменные окружения для backend
- `frontend/.env.local` - переменные окружения для frontend
- `docker-compose.yml` - настройки Docker

Примеры конфигурационных файлов см. в [SETUP.md](./docs/SETUP.md).

## 🤝 Вклад в проект

1. Fork проекта
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📝 Лицензия

[Указать лицензию]

## 👥 Авторы

[Указать авторов]

## 📞 Контакты

[Указать контакты]

---

**Примечание**: Для работы с ML-моделью требуется предварительное обучение или загрузка предобученной модели. Подробности в [ML_MODEL.md](./docs/ML_MODEL.md).

