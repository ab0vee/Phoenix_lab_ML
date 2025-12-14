# Скрипт для создания архива проекта без больших файлов
# Использование: .\create-archive.ps1

Write-Host "📦 Создание архива проекта Phoenix LAB..." -ForegroundColor Cyan

# Директории и файлы для исключения
$excludePatterns = @(
    'backend\ml_service\models_cache',
    'frontend\node_modules',
    '.next',
    '__pycache__',
    '*.log',
    '.env',
    '.git',
    '*.zip',
    '*.tar',
    '*.tar.gz',
    'docker-compose.override.yml'
)

# Имя архива
$archiveName = "Phoenix-LAB-Project-$(Get-Date -Format 'yyyy-MM-dd').zip"
$tempDir = "temp_archive"

# Удаляем старый архив, если есть
if (Test-Path $archiveName) {
    Remove-Item $archiveName -Force
    Write-Host "Удален старый архив" -ForegroundColor Yellow
}

# Удаляем временную директорию, если есть
if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}

# Создаем временную директорию
New-Item -ItemType Directory -Path $tempDir | Out-Null

Write-Host "Копирование файлов (исключая большие директории)..." -ForegroundColor Cyan

# Копируем файлы, исключая большие директории
Get-ChildItem -Path . -Recurse -File | ForEach-Object {
    $filePath = $_.FullName
    $relativePath = $_.FullName.Replace((Get-Location).Path + "\", "")
    $shouldExclude = $false
    
    # Проверяем, нужно ли исключить файл
    foreach ($pattern in $excludePatterns) {
        if ($relativePath -like "*$pattern*" -or $relativePath -like $pattern) {
            $shouldExclude = $true
            break
        }
    }
    
    if (-not $shouldExclude) {
        $destPath = Join-Path $tempDir $relativePath
        $destDir = Split-Path $destPath -Parent
        
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        
        Copy-Item $filePath -Destination $destPath -Force
    }
}

Write-Host "Создание ZIP архива..." -ForegroundColor Cyan

# Создаем ZIP архив
Compress-Archive -Path "$tempDir\*" -DestinationPath $archiveName -Force

# Удаляем временную директорию
Remove-Item $tempDir -Recurse -Force

# Получаем размер архива
$archiveSize = (Get-Item $archiveName).Length / 1MB

Write-Host "✅ Архив создан: $archiveName" -ForegroundColor Green
Write-Host "📊 Размер архива: $([math]::Round($archiveSize, 2)) MB" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Что включено в архив:" -ForegroundColor Cyan
Write-Host "  ✅ Весь исходный код" -ForegroundColor White
Write-Host "  ✅ Docker файлы (Dockerfile, docker-compose.yml)" -ForegroundColor White
Write-Host "  ✅ Конфигурационные файлы" -ForegroundColor White
Write-Host "  ✅ Документация" -ForegroundColor White
Write-Host ""
Write-Host "❌ Что НЕ включено (исключено):" -ForegroundColor Yellow
Write-Host "  ❌ backend\ml_service\models_cache\ (~24 GB)" -ForegroundColor White
Write-Host "  ❌ frontend\node_modules\ (~247 MB)" -ForegroundColor White
Write-Host "  ❌ .next\ (кэш Next.js)" -ForegroundColor White
Write-Host "  ❌ __pycache__\ (кэш Python)" -ForegroundColor White
Write-Host "  ❌ .env (переменные окружения)" -ForegroundColor White
Write-Host "  ❌ *.log (логи)" -ForegroundColor White
Write-Host ""
Write-Host "💡 Для получателя:" -ForegroundColor Cyan
Write-Host "  1. Распакуйте архив" -ForegroundColor White
Write-Host "  2. Создайте файл .env (см. HOW_TO_TRANSFER_PROJECT.md)" -ForegroundColor White
Write-Host "  3. Запустите: docker-compose up -d --build" -ForegroundColor White
Write-Host "  4. Модели скачаются автоматически при первом запуске" -ForegroundColor White

