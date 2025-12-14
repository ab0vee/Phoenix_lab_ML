#!/bin/bash
# Скрипт для создания архива проекта без больших файлов (Linux/Mac)
# Использование: ./create-archive.sh

echo "📦 Создание архива проекта Phoenix LAB..."

# Имя архива
ARCHIVE_NAME="Phoenix-LAB-Project-$(date +%Y-%m-%d).zip"
TEMP_DIR="temp_archive"

# Удаляем старый архив, если есть
if [ -f "$ARCHIVE_NAME" ]; then
    rm -f "$ARCHIVE_NAME"
    echo "Удален старый архив"
fi

# Удаляем временную директорию, если есть
if [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
fi

# Создаем временную директорию
mkdir -p "$TEMP_DIR"

echo "Копирование файлов (исключая большие директории)..."

# Копируем файлы, исключая большие директории
find . -type f ! -path "./backend/ml_service/models_cache/*" \
         ! -path "./frontend/node_modules/*" \
         ! -path "./.next/*" \
         ! -path "./__pycache__/*" \
         ! -path "./.git/*" \
         ! -name "*.log" \
         ! -name ".env" \
         ! -name "*.zip" \
         ! -name "*.tar" \
         ! -name "*.tar.gz" \
         ! -name "docker-compose.override.yml" \
         -exec sh -c 'mkdir -p "$1/$(dirname "$2")" && cp "$2" "$1/$2"' _ "$TEMP_DIR" {} \;

echo "Создание ZIP архива..."

# Создаем ZIP архив
cd "$TEMP_DIR"
zip -r "../$ARCHIVE_NAME" . > /dev/null
cd ..

# Удаляем временную директорию
rm -rf "$TEMP_DIR"

# Получаем размер архива
ARCHIVE_SIZE=$(du -h "$ARCHIVE_NAME" | cut -f1)

echo "✅ Архив создан: $ARCHIVE_NAME"
echo "📊 Размер архива: $ARCHIVE_SIZE"
echo ""
echo "📋 Что включено в архив:"
echo "  ✅ Весь исходный код"
echo "  ✅ Docker файлы (Dockerfile, docker-compose.yml)"
echo "  ✅ Конфигурационные файлы"
echo "  ✅ Документация"
echo ""
echo "❌ Что НЕ включено (исключено):"
echo "  ❌ backend/ml_service/models_cache/ (~24 GB)"
echo "  ❌ frontend/node_modules/ (~247 MB)"
echo "  ❌ .next/ (кэш Next.js)"
echo "  ❌ __pycache__/ (кэш Python)"
echo "  ❌ .env (переменные окружения)"
echo "  ❌ *.log (логи)"
echo ""
echo "💡 Для получателя:"
echo "  1. Распакуйте архив"
echo "  2. Создайте файл .env (см. HOW_TO_TRANSFER_PROJECT.md)"
echo "  3. Запустите: docker-compose up -d --build"
echo "  4. Модели скачаются автоматически при первом запуске"

