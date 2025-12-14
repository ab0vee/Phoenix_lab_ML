# 🔌 Инструкция по подключению готовой БД

Этот документ для **того, кто будет подключать уже подготовленную БД**.

## 📦 Что нужно получить от разработчика БД

1. **SQL дамп БД** (файл `.sql` или `.dump`)
   - Или готовый Docker volume с данными
   - Или инструкция по восстановлению из бэкапа

2. **Параметры подключения**:
   - Хост и порт
   - Имя базы данных
   - Пользователь и пароль
   - (Опционально) SSL настройки

3. **Версия схемы** (если используется версионирование миграций)

## 🚀 Варианты подключения

### Вариант 1: SQL дамп (рекомендуется)

#### Шаг 1: Получите файл дампа
Разработчик БД должен предоставить файл `phoenix_lab_dump.sql`

#### Шаг 2: Создайте БД и восстановите
```bash
# Создать базу данных
createdb phoenix_lab

# Восстановить из дампа
psql -d phoenix_lab < phoenix_lab_dump.sql
```

#### Через Docker:
```bash
# Если PostgreSQL в Docker
docker exec -i phoenix_postgres psql -U phoenix_user -d phoenix_lab < phoenix_lab_dump.sql
```

### Вариант 2: Docker volume (если БД в Docker)

#### Шаг 1: Получите архив volume
Разработчик должен предоставить:
- Архив с данными PostgreSQL volume
- Или инструкцию по копированию volume

#### Шаг 2: Восстановите volume
```bash
# Распакуйте архив
tar -xzf postgres_data.tar.gz

# Подключите volume в docker-compose.yml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./postgres_data
```

### Вариант 3: Прямое подключение к удаленной БД

Если БД находится на удаленном сервере:

#### Шаг 1: Обновите настройки подключения
В файле `.env` или `docker-compose.yml`:
```env
DATABASE_URL=postgresql://username:password@remote-host:5432/phoenix_lab
```

#### Шаг 2: Проверьте доступность
```bash
psql "postgresql://username:password@remote-host:5432/phoenix_lab" -c "SELECT version();"
```

## ⚙️ Настройка в проекте

### 1. Обновите `config.py` или `.env`

Создайте/обновите файл `.env` в `backend/ml_service/`:

```env
DATABASE_URL=postgresql://phoenix_user:your_password@localhost:5432/phoenix_lab
```

### 2. Обновите `docker-compose.yml`

Раскомментируйте и настройте PostgreSQL:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: phoenix_postgres
    environment:
      - POSTGRES_USER=phoenix_user
      - POSTGRES_PASSWORD=your_password
      - POSTGRES_DB=phoenix_lab
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U phoenix_user"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### 3. Установите зависимости (если еще не установлены)

```bash
cd backend/ml_service
pip install sqlalchemy psycopg2-binary alembic
```

Или добавьте в `requirements.txt`:
```
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
alembic>=1.12.0
```

## ✅ Проверка подключения

### Тест 1: Проверка через psql
```bash
psql -h localhost -U phoenix_user -d phoenix_lab -c "SELECT COUNT(*) FROM users;"
```

### Тест 2: Python скрипт
Создайте `test_db_connection.py`:

```python
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://phoenix_user:password@localhost:5432/phoenix_lab")

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        print(f"✅ Подключение успешно! Пользователей в БД: {count}")
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")
```

Запустите:
```bash
python test_db_connection.py
```

### Тест 3: Через API (если есть endpoint)
```bash
curl http://localhost:8000/api/v1/users
```

## 🔧 Решение проблем

### Ошибка: "relation does not exist"
**Причина**: Таблицы не созданы  
**Решение**: Выполните `schema.sql` или восстановите из дампа

### Ошибка: "password authentication failed"
**Причина**: Неверный пароль  
**Решение**: Проверьте `DATABASE_URL` в `.env`

### Ошибка: "could not connect to server"
**Причина**: PostgreSQL не запущен  
**Решение**: 
```bash
docker-compose up -d postgres
# или
sudo systemctl start postgresql
```

### Ошибка: "database does not exist"
**Причина**: База данных не создана  
**Решение**:
```bash
createdb phoenix_lab
# или через psql
psql -U postgres -c "CREATE DATABASE phoenix_lab;"
```

## 📞 Контакты

Если возникли проблемы с подключением, свяжитесь с разработчиком БД и предоставьте:
- Текст ошибки
- Версию PostgreSQL
- Способ подключения (локально/Docker/удаленно)

