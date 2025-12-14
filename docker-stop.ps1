# Скрипт остановки всех сервисов через Docker
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Phoenix LAB - Остановка Docker" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверка наличия docker-compose
$dockerComposeInstalled = Get-Command docker-compose -ErrorAction SilentlyContinue
if (-not $dockerComposeInstalled) {
    Write-Host "[ОШИБКА] docker-compose не установлен!" -ForegroundColor Red
    exit 1
}

Write-Host "Остановка контейнеров..." -ForegroundColor Yellow
docker-compose down

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[OK] Все контейнеры остановлены!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[ОШИБКА] Не удалось остановить контейнеры!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Для удаления volumes используйте: docker-compose down -v" -ForegroundColor Cyan
Write-Host ""

