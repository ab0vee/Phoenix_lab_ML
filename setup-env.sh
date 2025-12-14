#!/bin/bash
# Автоматическое создание .env файла из .env.example
# Использование: ./setup-env.sh

echo "🔧 Настройка .env файла..."

if [ -f ".env" ]; then
    echo "⚠️  Файл .env уже существует"
    read -p "Перезаписать? (y/N): " overwrite
    if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
        echo "Отменено. Используется существующий .env файл."
        exit
    fi
fi

if [ ! -f ".env.example" ]; then
    echo "❌ Файл .env.example не найден!"
    exit 1
fi

# Копируем .env.example в .env
cp ".env.example" ".env"

# Создаем openrouter.env если его нет
if [ ! -f "backend/rewrite_service/openrouter.env" ]; then
    if [ -f "backend/rewrite_service/openrouter.env.example" ]; then
        cp "backend/rewrite_service/openrouter.env.example" "backend/rewrite_service/openrouter.env"
        echo "✅ Создан backend/rewrite_service/openrouter.env"
    fi
fi

# Создаем yandex.env если его нет
if [ ! -f "backend/rewrite_service/yandex.env" ]; then
    if [ -f "backend/rewrite_service/yandex.env.example" ]; then
        cp "backend/rewrite_service/yandex.env.example" "backend/rewrite_service/yandex.env"
        echo "✅ Создан backend/rewrite_service/yandex.env"
    fi
fi

echo "✅ Файл .env создан из .env.example"
echo ""
echo "📝 Все ключи скопированы. Можно запускать docker-compose."

