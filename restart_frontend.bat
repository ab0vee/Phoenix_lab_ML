@echo off
chcp 65001 >nul
echo ========================================
echo Полная очистка и перезапуск Frontend
echo ========================================
echo.

cd /d "%~dp0frontend"

echo [1/5] Остановка всех процессов Node.js на порту 3000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do (
    echo   Останавливаю процесс %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo [2/5] Ожидание освобождения порта...
timeout /t 3 /nobreak >nul

echo [3/5] Очистка кэша Next.js...
if exist .next (
    rmdir /s /q .next
    echo   Кэш .next удален
) else (
    echo   Кэш .next отсутствует
)

if exist node_modules\.cache (
    rmdir /s /q node_modules\.cache
    echo   Кэш node_modules удален
)

echo [4/5] Проверка файлов...
if exist "app\page.tsx" (
    echo   Файл page.tsx найден
) else (
    echo   ОШИБКА: Файл page.tsx не найден!
    pause
    exit /b 1
)

if exist "app\components\SettingsMenu.tsx" (
    echo   Файл SettingsMenu.tsx найден
) else (
    echo   ОШИБКА: Файл SettingsMenu.tsx не найден!
    pause
    exit /b 1
)

echo [5/5] Запуск dev сервера...
echo.
echo ========================================
echo Сервер запускается на http://localhost:3000
echo ========================================
echo.
echo После запуска:
echo   1. Откройте http://localhost:3000
echo   2. Нажмите Ctrl + Shift + R (жесткая перезагрузка)
echo   3. Кнопка "Настройки" должна быть в правом верхнем углу
echo.
echo Нажмите Ctrl+C для остановки сервера
echo.

npm run dev

pause

