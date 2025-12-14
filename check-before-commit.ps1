# Скрипт проверки перед коммитом в Git
# Использование: .\check-before-commit.ps1

Write-Host "🔍 Проверка перед коммитом..." -ForegroundColor Cyan
Write-Host ""

$errors = 0
$maxSize = 5MB  # Максимальный размер файла 5 MB

# Проверка 1: Модели не должны быть в staging
Write-Host "1. Проверка models_cache/..." -ForegroundColor Yellow
$stagedModels = git diff --cached --name-only | Select-String "models_cache/"
if ($stagedModels) {
    Write-Host "❌ ОШИБКА: models_cache/ найден в staging!" -ForegroundColor Red
    Write-Host "   Файлы:" -ForegroundColor Yellow
    $stagedModels | ForEach-Object { Write-Host "   - $_" -ForegroundColor Yellow }
    Write-Host ""
    Write-Host "   Решение: Убери из staging:" -ForegroundColor Yellow
    Write-Host "   git reset HEAD models_cache/" -ForegroundColor Cyan
    $errors++
} else {
    Write-Host "✅ models_cache/ не в staging" -ForegroundColor Green
}

# Проверка 2: Большие файлы
Write-Host ""
Write-Host "2. Проверка размера файлов..." -ForegroundColor Yellow
$largeFiles = git diff --cached --name-only | ForEach-Object {
    if (Test-Path $_) {
        $file = Get-Item $_
        if ($file.Length -gt $maxSize) {
            [PSCustomObject]@{
                File = $_
                Size = [math]::Round($file.Length / 1MB, 2)
            }
        }
    }
}

if ($largeFiles) {
    Write-Host "❌ ОШИБКА: Найдены большие файлы (>5 MB):" -ForegroundColor Red
    $largeFiles | ForEach-Object {
        Write-Host "   - $($_.File): $($_.Size) MB" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "   Решение: Добавь в .gitignore или используй Git LFS" -ForegroundColor Yellow
    $errors++
} else {
    Write-Host "✅ Все файлы меньше 5 MB" -ForegroundColor Green
}

# Проверка 3: Проверка .bin и .safetensors файлов
Write-Host ""
Write-Host "3. Проверка ML моделей (.bin, .safetensors)..." -ForegroundColor Yellow
$modelFiles = git diff --cached --name-only | Where-Object {
    $_ -match "\.(bin|safetensors|pth|pt)$"
}

if ($modelFiles) {
    Write-Host "❌ ОШИБКА: Найдены файлы моделей в staging:" -ForegroundColor Red
    $modelFiles | ForEach-Object { Write-Host "   - $_" -ForegroundColor Yellow }
    Write-Host ""
    Write-Host "   Решение: Эти файлы не должны быть в Git!" -ForegroundColor Yellow
    Write-Host "   git reset HEAD $($modelFiles -join ' ')" -ForegroundColor Cyan
    $errors++
} else {
    Write-Host "✅ Файлы моделей не найдены в staging" -ForegroundColor Green
}

# Проверка 4: Размер репозитория
Write-Host ""
Write-Host "4. Проверка размера репозитория..." -ForegroundColor Yellow
$repoSize = (git count-objects -vH | Select-String "size-pack:" | ForEach-Object { ($_ -split ":")[1].Trim() })
Write-Host "   Размер .git: $repoSize" -ForegroundColor Cyan

if ($repoSize -match "(\d+)\s*(M|G)") {
    $size = [int]$matches[1]
    $unit = $matches[2]
    
    if ($unit -eq "G" -or ($unit -eq "M" -and $size -gt 100)) {
        Write-Host "⚠️  Предупреждение: Репозиторий большой ($repoSize)" -ForegroundColor Yellow
        Write-Host "   Проверь что модели не были закоммичены ранее" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Размер репозитория нормальный" -ForegroundColor Green
    }
}

# Итог
Write-Host ""
if ($errors -eq 0) {
    Write-Host "✨ Всё хорошо! Можно коммитить" -ForegroundColor Green
    Write-Host ""
    Write-Host "Следующий шаг:" -ForegroundColor Cyan
    Write-Host "git commit -m 'Your commit message'" -ForegroundColor White
    exit 0
} else {
    Write-Host "❌ Найдено $errors ошибок. Исправь их перед коммитом!" -ForegroundColor Red
    exit 1
}




