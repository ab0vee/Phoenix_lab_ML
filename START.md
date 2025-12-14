# 🚀 Запуск Phoenix LAB

## Вариант 1: Docker Compose (рекомендуется)

### Быстрый старт

1. **Создайте файл `.env`** (скопируйте из `ENV_VARIABLES_COMPLETE.txt` и заполните минимально необходимые ключи):
   ```bash
   API_KEY=your-api-key-here
   OPENROUTER_API_KEY=your-openrouter-key
   YANDEX_CLOUD_API_KEY=your-yandex-key
   BOT_TOKEN=your-telegram-bot-token
   ```

2. **Запустите все сервисы:**
   ```bash
   # Windows
   docker-start.bat
   
   # Linux/Mac
   ./docker-start.sh
   
   # Или вручную
   docker-compose up -d
   ```

3. **Откройте в браузере:** http://localhost:3000

### Команды управления

```bash
# Просмотр статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Пересборка после изменений
docker-compose up -d --build
```

## Вариант 2: Локальный запуск (для разработки)

### Требования
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis (опционально)

### Запуск

1. **База данных и Redis (через Docker):**
   ```bash
   docker-compose up -d postgres redis
   ```

2. **ML Service:**
   ```bash
   cd backend/ml_service
   pip install -r requirements.txt
   python main.py
   ```

3. **Rewrite Service:**
   ```bash
   cd backend/rewrite_service
   pip install -r requirements.txt
   python server.py
   ```

4. **Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Telegram Bot (опционально):**
   ```bash
   cd backend/telegram_bot
   pip install -r requirements.txt
   python main.py
   ```

## Структура сервисов

| Сервис | Порт | URL |
|--------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Rewrite Service | 5000 | http://localhost:5000 |
| ML Service | 8000 | http://localhost:8000 |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |

## Минимальные требования для Docker

- Docker Desktop / Docker Engine
- 8 GB RAM
- 10 GB свободного места
- Интернет (для загрузки моделей при первом запуске)

## Первый запуск

При первом запуске ML Service автоматически скачает модели (~2-3 GB). Это может занять 10-30 минут.

Модели кэшируются в Docker volume, поэтому при последующих запусках загрузка не требуется.

## Документация

- **Полная документация Docker:** `README_DOCKER.md`
- **Быстрый старт:** `QUICK_START.md`
- **Переменные окружения:** `ENV_VARIABLES_COMPLETE.txt`


