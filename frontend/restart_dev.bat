@echo off
echo ========================================
echo Очистка и перезапуск Next.js dev сервера
echo ========================================
echo.

echo [1/4] Остановка всех процессов Node.js на порту 3000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do (
    echo Останавливаю процесс %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo [2/4] Ожидание освобождения порта...
timeout /t 2 /nobreak >nul

echo [3/4] Очистка кэша Next.js...
if exist .next (
    rmdir /s /q .next
    echo Кэш .next удален
)

echo [4/4] Запуск dev сервера...
echo.
echo Сервер запускается на http://localhost:3000
echo Нажмите Ctrl+C для остановки
echo.

npm run dev

