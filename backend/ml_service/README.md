# ML Service - Phoenix LAB

Сервис для парафразирования и суммаризации новостных текстов.

## Установка

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
# Отредактируйте .env с вашими настройками
```

## Запуск

```bash
python main.py
```

Или через uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

- `GET /health` - Проверка состояния сервиса
- `POST /api/v1/paraphrase` - Парафразирование текста
- `POST /api/v1/summarize` - Суммаризация текста
- `POST /api/v1/process` - Полная обработка (fetch + summarize + paraphrase)
- `POST /api/v1/similarity` - Проверка схожести текстов

## Документация API

После запуска доступна по адресу:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Структура проекта

```
ml_service/
├── api/
│   ├── routes/          # API endpoints
│   ├── schemas.py       # Pydantic схемы
│   └── dependencies.py  # Зависимости (auth, etc)
├── services/            # Бизнес-логика
│   ├── content_extractor.py
│   └── text_processor.py
├── models/              # ML модели (TODO)
├── utils/               # Утилиты
├── models_cache/        # Кэш моделей
├── config.py            # Конфигурация
└── main.py              # Точка входа
```

## TODO

- [ ] Интеграция реальных ML моделей
- [ ] Кэширование через Redis
- [ ] Подключение к базе данных
- [ ] Логирование и мониторинг
- [ ] Тесты

