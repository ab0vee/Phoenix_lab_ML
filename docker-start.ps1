# Скрипт запуска всех сервисов через Docker
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Phoenix LAB - Запуск через Docker" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверка наличия Docker
$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerInstalled) {
    Write-Host "[ОШИБКА] Docker не установлен!" -ForegroundColor Red
    Write-Host "Установите Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Проверка наличия docker-compose
$dockerComposeInstalled = Get-Command docker-compose -ErrorAction SilentlyContinue
if (-not $dockerComposeInstalled) {
    Write-Host "[ОШИБКА] docker-compose не установлен!" -ForegroundColor Red
    exit 1
}

# Проверка, что Docker запущен
try {
    docker ps | Out-Null
} catch {
    Write-Host "[ОШИБКА] Docker не запущен!" -ForegroundColor Red
    Write-Host "Запустите Docker Desktop и попробуйте снова." -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/3] Сборка образов..." -ForegroundColor Green
docker-compose build

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ОШИБКА] Не удалось собрать образы!" -ForegroundColor Red
    exit 1
}

Write-Host "[2/3] Запуск контейнеров..." -ForegroundColor Green
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ОШИБКА] Не удалось запустить контейнеры!" -ForegroundColor Red
    exit 1
}

Write-Host "[3/3] Проверка статуса..." -ForegroundColor Green
Start-Sleep -Seconds 5
docker-compose ps

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Все сервисы запущены!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend:        http://localhost:3000" -ForegroundColor Yellow
Write-Host "Rewrite Service: http://localhost:5000" -ForegroundColor Yellow
Write-Host "ML Service:      http://localhost:8000" -ForegroundColor Yellow
Write-Host "PostgreSQL:      localhost:5432" -ForegroundColor Yellow
Write-Host "Redis:           localhost:6379" -ForegroundColor Yellow
Write-Host ""
Write-Host "Просмотр логов:  docker-compose logs -f" -ForegroundColor Cyan
Write-Host "Остановка:       docker-compose down" -ForegroundColor Cyan
Write-Host ""

