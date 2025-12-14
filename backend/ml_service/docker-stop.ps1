# Скрипт для остановки ML Service в Docker
# Использование: .\docker-stop.ps1

Write-Host "🛑 Остановка Phoenix LAB ML Service..." -ForegroundColor Yellow
docker-compose down

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Сервис остановлен" -ForegroundColor Green
} else {
    Write-Host "❌ Ошибка при остановке" -ForegroundColor Red
}




