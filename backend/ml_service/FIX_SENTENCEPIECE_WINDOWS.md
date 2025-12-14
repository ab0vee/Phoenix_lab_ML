# Исправление ошибки sentencepiece на Windows

## Проблема
`sentencepiece` требует компилятор C++ для сборки на Windows, что вызывает ошибку:
```
FileNotFoundError: [WinError 2] Не удается найти указанный файл
```

## Решения

### Вариант 1: Использовать предкомпилированные wheels (рекомендуется)

Попробуйте установить предкомпилированную версию:

```bash
pip install sentencepiece --only-binary :all:
```

Или установите через conda (если установлен):
```bash
conda install -c conda-forge sentencepiece
```

### Вариант 2: Установить Visual Studio Build Tools

1. Скачайте и установите [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)
2. При установке выберите "C++ build tools"
3. После установки перезапустите терминал
4. Попробуйте установить снова: `pip install sentencepiece`

### Вариант 3: Использовать Docker (самый простой)

ML Service уже настроен для работы в Docker, где все зависимости установлены:

```bash
cd backend/ml_service
docker-compose up -d
```

### Вариант 4: Использовать requirements-minimal.txt

Если `sentencepiece` не критичен для ваших моделей, используйте минимальный набор зависимостей:

```bash
pip install -r requirements-minimal.txt
```

**Примечание:** Некоторые модели T5 могут требовать `sentencepiece`. Если модель не работает, используйте Docker или установите Build Tools.

## Проверка

После установки проверьте:
```python
import sentencepiece
print("sentencepiece установлен успешно")
```

