@echo off
chcp 65001 >nul
echo ========================================
echo   Phoenix LAB - Запуск всех сервисов
echo ========================================
echo.

:: Проверяем, что мы в корневой директории проекта
if not exist "backend\rewrite_service\server.py" (
    echo [ОШИБКА] Файл backend\rewrite_service\server.py не найден!
    echo Убедитесь, что вы запускаете скрипт из корневой директории проекта.
    pause
    exit /b 1
)

:: Проверяем наличие Node.js
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] Node.js не установлен или не найден в PATH!
    echo Установите Node.js: https://nodejs.org/
    pause
    exit /b 1
)

:: Проверяем наличие Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] Python не установлен или не найден в PATH!
    echo Установите Python: https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Проверка зависимостей...
echo.

:: Проверяем node_modules во Frontend
if not exist "frontend\node_modules" (
    echo [ВНИМАНИЕ] node_modules не найдены. Устанавливаю зависимости Frontend...
    cd frontend
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo [ОШИБКА] Не удалось установить зависимости Node.js
        cd ..
        pause
        exit /b 1
    )
    cd ..
)

:: Проверяем зависимости Python для Rewrite Service
echo [INFO] Проверка зависимостей Rewrite Service...
cd backend\rewrite_service
python -c "import flask" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ВНИМАНИЕ] Устанавливаю зависимости Rewrite Service...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [ОШИБКА] Не удалось установить зависимости Rewrite Service
        cd ..\..
        pause
        exit /b 1
    )
)
cd ..\..

:: Проверяем зависимости Python для Telegram Bot
echo [INFO] Проверка зависимостей Telegram Bot...
cd backend\telegram_bot
python -c "import aiogram" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ВНИМАНИЕ] Устанавливаю зависимости Telegram Bot...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [ОШИБКА] Не удалось установить зависимости Telegram Bot
        cd ..\..
        pause
        exit /b 1
    )
)
cd ..\..

echo [2/5] Запуск Frontend (Next.js)...
start "Phoenix LAB - Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev"
timeout /t 3 /nobreak >nul

echo [3/5] Запуск Rewrite Service (Flask)...
start "Phoenix LAB - Rewrite Service" cmd /k "cd /d %~dp0\backend\rewrite_service && python server.py"
timeout /t 3 /nobreak >nul

echo [4/5] Запуск Telegram Bot...
start "Phoenix LAB - Telegram Bot" cmd /k "cd /d %~dp0\backend\telegram_bot && python main.py"
timeout /t 2 /nobreak >nul

echo [5/5] ML Service (Docker)...
echo [INFO] ML Service запускается через Docker
echo [INFO] Для запуска ML Service используйте:
echo        cd backend\ml_service
echo        docker-compose up -d
echo.

echo ========================================
echo   Все сервисы запущены!
echo ========================================
echo.
echo Frontend:        http://localhost:3000
echo Rewrite Service: http://localhost:5000
echo ML Service:      http://localhost:8000 (запускается отдельно через Docker)
echo Telegram Bot:    Запущен и ожидает команды
echo.
echo Для остановки закройте окна с сервисами
echo или используйте stop_all.bat
echo.
pause

