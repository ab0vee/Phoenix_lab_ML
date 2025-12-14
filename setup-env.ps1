# Автоматическое создание .env файла из .env.example
# Использование: .\setup-env.ps1

Write-Host "🔧 Настройка .env файла..." -ForegroundColor Cyan

if (Test-Path ".env") {
    Write-Host "⚠️  Файл .env уже существует" -ForegroundColor Yellow
    $overwrite = Read-Host "Перезаписать? (y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Host "Отменено. Используется существующий .env файл." -ForegroundColor Yellow
        exit
    }
}

if (-not (Test-Path ".env.example")) {
    Write-Host "❌ Файл .env.example не найден!" -ForegroundColor Red
    exit 1
}

# Копируем .env.example в .env
Copy-Item ".env.example" ".env" -Force

# Создаем openrouter.env если его нет
if (-not (Test-Path "backend/rewrite_service/openrouter.env")) {
    if (Test-Path "backend/rewrite_service/openrouter.env.example") {
        Copy-Item "backend/rewrite_service/openrouter.env.example" "backend/rewrite_service/openrouter.env" -Force
        Write-Host "✅ Создан backend/rewrite_service/openrouter.env" -ForegroundColor Green
    }
}

# Создаем yandex.env если его нет
if (-not (Test-Path "backend/rewrite_service/yandex.env")) {
    if (Test-Path "backend/rewrite_service/yandex.env.example") {
        Copy-Item "backend/rewrite_service/yandex.env.example" "backend/rewrite_service/yandex.env" -Force
        Write-Host "✅ Создан backend/rewrite_service/yandex.env" -ForegroundColor Green
    }
}

Write-Host "✅ Файл .env создан из .env.example" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Все ключи скопированы. Можно запускать docker-compose." -ForegroundColor Cyan

