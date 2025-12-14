# Скрипт проверки установки Docker
Write-Host "🔍 Проверка установки Docker..." -ForegroundColor Cyan
Write-Host ""

# Проверка Docker
Write-Host "Проверка Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker установлен: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker не найден!" -ForegroundColor Red
    Write-Host "   Убедись, что Docker Desktop запущен" -ForegroundColor Yellow
    exit 1
}

# Проверка Docker Compose
Write-Host "Проверка Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose установлен: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose не найден!" -ForegroundColor Red
    exit 1
}

# Проверка работы Docker
Write-Host "Проверка работы Docker..." -ForegroundColor Yellow
try {
    docker ps > $null 2>&1
    Write-Host "✅ Docker работает!" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker не работает!" -ForegroundColor Red
    Write-Host "   Запусти Docker Desktop и попробуй снова" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "✨ Всё готово! Docker установлен и работает" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Следующий шаг: запусти .\docker-start.ps1" -ForegroundColor Cyan




