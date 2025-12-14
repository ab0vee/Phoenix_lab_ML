# Скрипт для просмотра логов ML Service
# Использование: .\docker-logs.ps1

Write-Host "📋 Логи Phoenix LAB ML Service" -ForegroundColor Cyan
Write-Host "Нажмите Ctrl+C для выхода" -ForegroundColor Yellow
Write-Host ""

docker-compose logs -f




