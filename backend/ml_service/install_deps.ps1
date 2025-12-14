# Скрипт установки зависимостей для Windows
# Использует уже установленные пакеты где возможно

Write-Host "Установка зависимостей для ML Service..." -ForegroundColor Green

# Обновление pip
python -m pip install --upgrade pip setuptools wheel

# Установка pydantic (если еще не установлен)
Write-Host "Проверка pydantic..." -ForegroundColor Yellow
pip show pydantic > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Установка pydantic..." -ForegroundColor Yellow
    pip install "pydantic>=2.5.0" "pydantic-settings>=2.1.0"
}

# Установка основных зависимостей
Write-Host "Установка основных зависимостей..." -ForegroundColor Yellow
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 python-multipart==0.0.6

# HTTP клиенты
Write-Host "Установка HTTP клиентов..." -ForegroundColor Yellow
pip install httpx==0.25.2 aiohttp==3.9.1

# Извлечение контента
Write-Host "Установка библиотек для извлечения контента..." -ForegroundColor Yellow
pip install trafilatura==1.6.3 readability-lxml==0.8.1 beautifulsoup4==4.12.2 lxml==4.9.3

# Утилиты
Write-Host "Установка утилит..." -ForegroundColor Yellow
pip install python-dotenv==1.0.0 langdetect==1.0.9

# Логирование
Write-Host "Установка библиотек логирования..." -ForegroundColor Yellow
pip install structlog==23.2.0

Write-Host "`nГотово! Зависимости установлены." -ForegroundColor Green
Write-Host "Для проверки запустите: python main.py" -ForegroundColor Cyan

