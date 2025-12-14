@echo off
chcp 65001 >nul
echo ========================================
echo   Phoenix LAB - Остановка всех сервисов
echo ========================================
echo.

:: Останавливаем процессы Node.js (Next.js Frontend)
echo [1/4] Остановка Frontend (Next.js)...
taskkill /F /IM node.exe >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Frontend остановлен
) else (
    echo [INFO] Frontend не был запущен
)

:: Останавливаем процессы Python по окнам
echo [2/4] Остановка Rewrite Service и Telegram Bot...
taskkill /F /FI "WINDOWTITLE eq Phoenix LAB - Rewrite Service*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Phoenix LAB - Telegram Bot*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Phoenix LAB - Frontend*" >nul 2>&1

:: Останавливаем ML Service (Docker)
echo [3/4] Остановка ML Service (Docker)...
cd backend\ml_service
docker-compose down >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] ML Service остановлен
) else (
    echo [INFO] ML Service не был запущен или Docker не установлен
)
cd ..\..

:: Дополнительная очистка процессов Python (на случай, если что-то осталось)
echo [4/4] Финальная очистка...
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST 2^>nul ^| findstr /C:"PID:"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo ========================================
echo   Все сервисы остановлены!
echo ========================================
echo.
pause

