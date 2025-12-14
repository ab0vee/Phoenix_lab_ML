# Скрипт для запуска ML Service в Docker
# Использование: .\docker-start.ps1

Write-Host "🐳 Phoenix LAB ML Service - Docker Start" -ForegroundColor Cyan
Write-Host ""

# Проверка установки Docker
Write-Host "Проверка Docker..." -ForegroundColor Yellow
$dockerVersion = docker --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker не установлен!" -ForegroundColor Red
    Write-Host "Скачайте Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Docker установлен: $dockerVersion" -ForegroundColor Green

# Проверка Docker Compose
$composeVersion = docker-compose --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker Compose не установлен!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker Compose установлен: $composeVersion" -ForegroundColor Green
Write-Host ""

# Остановка старых контейнеров
Write-Host "Остановка старых контейнеров..." -ForegroundColor Yellow
docker-compose down 2>$null
Write-Host ""

# Сборка образа
Write-Host "🔨 Сборка Docker образа..." -ForegroundColor Cyan
Write-Host "Это может занять 10-15 минут при первом запуске..." -ForegroundColor Yellow
docker-compose build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при сборке образа!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Образ собран успешно" -ForegroundColor Green
Write-Host ""

# Запуск контейнеров
Write-Host "🚀 Запуск контейнеров..." -ForegroundColor Cyan
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при запуске контейнеров!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Контейнеры запущены" -ForegroundColor Green
Write-Host ""

# Ожидание запуска
Write-Host "⏳ Ожидание запуска сервиса (30 секунд)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Проверка здоровья
Write-Host "🏥 Проверка здоровья сервиса..." -ForegroundColor Yellow
$health = curl -s http://localhost:8000/health 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Сервис работает!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Сервис ещё запускается. Проверьте через минуту." -ForegroundColor Yellow
}
Write-Host ""

# Информация
Write-Host "📋 Информация:" -ForegroundColor Cyan
Write-Host "  Тестовая страница: http://localhost:8000/test" -ForegroundColor White
Write-Host "  Swagger UI:        http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Health Check:      http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "📊 Полезные команды:" -ForegroundColor Cyan
Write-Host "  Логи:              docker-compose logs -f" -ForegroundColor White
Write-Host "  Остановка:         docker-compose down" -ForegroundColor White
Write-Host "  Перезапуск:        docker-compose restart" -ForegroundColor White
Write-Host "  Статус:            docker ps" -ForegroundColor White
Write-Host ""
Write-Host "✨ Готово! Откройте http://localhost:8000/test в браузере" -ForegroundColor Green




