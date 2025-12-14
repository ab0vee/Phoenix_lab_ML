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

Write-Host "✅ Файл .env создан из .env.example" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Теперь отредактируйте .env файл и добавьте:" -ForegroundColor Yellow
Write-Host "   - BOT_TOKEN (Telegram Bot Token)" -ForegroundColor White
Write-Host "   - OPENROUTER_API_KEY (для Qwen модели)" -ForegroundColor White
Write-Host "   - API_KEY (любой случайный ключ для защиты API)" -ForegroundColor White
Write-Host ""
Write-Host "Остальные ключи опциональны и имеют значения по умолчанию." -ForegroundColor Cyan

