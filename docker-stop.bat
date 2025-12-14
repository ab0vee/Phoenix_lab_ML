@echo off
chcp 65001 >nul
echo ========================================
echo   Phoenix LAB - Остановка Docker
echo ========================================
echo.

echo Остановка контейнеров...
docker-compose down

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Все контейнеры остановлены!
) else (
    echo.
    echo [ОШИБКА] Не удалось остановить контейнеры!
    pause
    exit /b 1
)

echo.
echo Для удаления volumes используйте: docker-compose down -v
echo.
pause

