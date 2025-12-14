# YandexGPT API - Документация

## Обзор

YandexGPT — это генеративная языковая модель от Яндекс, доступная через Yandex Cloud API. В проекте Phoenix LAB она используется для рерайта статей в различных стилях.

## Настройка

### 1. Получение API ключа

1. Зарегистрируйтесь в [Yandex Cloud](https://cloud.yandex.ru/)
2. Создайте сервисный аккаунт с ролью `ai.languageModels.user`
3. Сгенерируйте API-ключ в разделе "Сервисные аккаунты"

### 2. Конфигурация в проекте

Добавьте следующие переменные в `.env` файл в корне проекта:

```env
YANDEX_CLOUD_API_KEY=your_api_key_here
YANDEX_CLOUD_PROJECT=your_folder_id_here
YANDEX_CLOUD_ASSISTANT_ID=your_assistant_id_here
```

Или используйте файл `backend/rewrite_service/yandex.env`:

```env
YANDEX_CLOUD_API_KEY=your_api_key_here
YANDEX_CLOUD_PROJECT=b1goig30m707ojip72c7
YANDEX_CLOUD_ASSISTANT_ID=fvtfdp5dm8r044bnumjl
```

### 3. Проверка настройки

После добавления переменных перезапустите сервис:

```bash
docker-compose restart rewrite_service
```

Проверьте логи:

```bash
docker logs phoenix_rewrite_service | grep YandexGPT
```

Должно появиться сообщение:
```
✅ YandexGPT API клиент инициализирован
```

## Использование

### Через Frontend

1. Откройте главную страницу (http://localhost:3000)
2. Введите URL статьи
3. Выберите стиль рерайта
4. В настройках (иконка шестеренки) выберите "Yandex Алиса" в разделе "РЕРАЙТ"
5. Нажмите "Обработать"

### Через API

```bash
POST http://localhost:5000/api/rewrite-article
Content-Type: application/json

{
  "url": "https://example.com/article",
  "style": "casual",
  "provider": "yandex"
}
```

## Доступные стили

- **scientific** — Научно-деловой стиль
- **meme** — Мемный стиль
- **casual** — Повседневный стиль

## Технические детали

### Endpoint API

- **Base URL**: `https://rest-assistant.api.cloud.yandex.net/v1`
- **Метод**: `POST /responses/create`
- **Аутентификация**: API Key в заголовке `Authorization`

### Заголовки запроса

```
Authorization: Api-Key <YANDEX_CLOUD_API_KEY>
x-folder-id: <YANDEX_CLOUD_PROJECT>
Content-Type: application/json
```

### Формат запроса

```json
{
  "prompt": {
    "id": "<YANDEX_CLOUD_ASSISTANT_ID>"
  },
  "input": "<текст для обработки>"
}
```

### Формат ответа

```json
{
  "output_text": "<обработанный текст>"
}
```

## Ограничения

- Максимальная длина входного текста: 12000 символов
- Токены действительны бессрочно (пока пользователь авторизован)
- Требуется подключение к интернету

## Устранение неполадок

### Ошибка: "YandexGPT API не настроен"

**Причина**: API ключ не найден или не загружен

**Решение**:
1. Проверьте, что переменная `YANDEX_CLOUD_API_KEY` указана в `.env`
2. Убедитесь, что файл `.env` находится в корне проекта
3. Перезапустите сервис: `docker-compose restart rewrite_service`

### Ошибка: "Ошибка инициализации YandexGPT API"

**Причина**: Проблема с библиотекой `openai` или неправильный API ключ

**Решение**:
1. Проверьте версию библиотеки: должна быть `openai>=1.40.0`
2. Проверьте правильность API ключа
3. Проверьте логи: `docker logs phoenix_rewrite_service | grep YandexGPT`

### Ошибка: "Ошибка подключения к YandexGPT API"

**Причина**: Проблемы с сетью или неверный endpoint

**Решение**:
1. Проверьте подключение к интернету
2. Убедитесь, что API ключ действителен
3. Проверьте, что `YANDEX_CLOUD_PROJECT` указан правильно

## Дополнительные ресурсы

- [Официальная документация YandexGPT](https://yandex.cloud/ru/docs/foundation-models/quickstart/yandexgpt)
- [Руководство по промптингу](https://yandex.cloud/ru/docs/ai-studio/gpt-prompting-guide/popular-problems-solving)
- [OpenAI-совместимый API](https://yandex.cloud/ru/docs/ai-studio/concepts/openai-compatibility)

## Версия библиотеки

Проект использует `openai>=1.40.0` для работы с YandexGPT API через OpenAI-совместимый интерфейс.



