@echo off
REM Скрипт для запуска всех сервисов через Docker Compose (Windows)

echo 🚀 Запуск Phoenix LAB через Docker Compose...

REM Проверяем наличие .env файла
if not exist .env (
    echo ⚠️  Файл .env не найден!
    echo 📝 Создайте файл .env на основе .env.example
    echo    Или используйте значения по умолчанию (некоторые функции могут не работать)
    pause
)

REM Запускаем все сервисы
docker-compose up -d

REM Ждем немного для инициализации
echo ⏳ Ожидание инициализации сервисов...
timeout /t 5 /nobreak >nul

REM Проверяем статус
echo.
echo 📊 Статус сервисов:
docker-compose ps

echo.
echo ✅ Сервисы запущены!
echo.
echo 🌐 Доступные сервисы:
echo    - Frontend:        http://localhost:3000
echo    - Rewrite Service:  http://localhost:5000
echo    - ML Service:      http://localhost:8000
echo    - PostgreSQL:      localhost:5432
echo.
echo 📋 Просмотр логов: docker-compose logs -f
echo 🛑 Остановка:     docker-compose down
pause
