@echo off
chcp 65001 >nul
echo ========================================
echo   Установка зависимостей Telegram Bot
echo ========================================
echo.

:: Проверка Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] Python не найден!
    echo Установите Python: https://www.python.org/
    pause
    exit /b 1
)

echo [1/3] Обновление pip, setuptools, wheel...
python -m pip install --upgrade pip setuptools wheel
if %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] Не удалось обновить pip
    pause
    exit /b 1
)

echo.
echo [2/3] Установка зависимостей (только бинарные пакеты)...
pip install --only-binary :all: -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ПРЕДУПРЕЖДЕНИЕ] Установка с --only-binary не удалась
    echo Попробую обычную установку...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [ОШИБКА] Не удалось установить зависимости
        echo.
        echo Рекомендация: Используйте Docker
        echo docker-compose up -d telegram_bot
        pause
        exit /b 1
    )
)

echo.
echo [3/3] Проверка установки...
python -c "import aiogram; print('✅ aiogram установлен')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] aiogram не установлен
    pause
    exit /b 1
)

python -c "import pydantic; print('✅ pydantic установлен')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ПРЕДУПРЕЖДЕНИЕ] pydantic не установлен, но это может быть нормально
)

echo.
echo ========================================
echo   ✅ Зависимости установлены!
echo ========================================
echo.
echo Теперь можно запустить бота:
echo python main.py
echo.
pause

