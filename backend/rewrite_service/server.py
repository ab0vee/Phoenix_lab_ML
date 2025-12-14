from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import logging
import asyncio
import re
import requests
import secrets
import time
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import html as html_module

# Опциональный импорт aiogram (нужен только для отправки статей)
try:
    from aiogram import Bot
    from aiogram.exceptions import TelegramAPIError
    from aiogram.types import InputFile
    AIOGRAM_AVAILABLE = True
except ImportError:
    AIOGRAM_AVAILABLE = False

# Опциональный импорт AsyncKandinsky для генерации изображений
try:
    from AsyncKandinsky import FusionBrainApi, ApiApi, ApiWeb
    KANDINSKY_AVAILABLE = True
except ImportError:
    KANDINSKY_AVAILABLE = False

# Загружаем .env из корня проекта
# BASE_DIR теперь указывает на корень проекта (на уровень выше backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(BASE_DIR, '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(BASE_DIR, 'BOT_TOKEN.env')
    # Если файл BOT_TOKEN.env существует, загружаем его
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
    else:
        load_dotenv()
else:
    load_dotenv(env_path)

# Загружаем openrouter.env если существует (теперь в backend/rewrite_service)
openrouter_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'openrouter.env')
if os.path.exists(openrouter_env_path):
    load_dotenv(openrouter_env_path, override=True)

# Загружаем yandex.env если существует (теперь в backend/rewrite_service)
yandex_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'yandex.env')
if os.path.exists(yandex_env_path):
    load_dotenv(yandex_env_path, override=True)

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для запросов с сайта

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Опциональный импорт OpenAI для YandexGPT
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI не установлен. YandexGPT будет недоступен. Установите: pip install openai")

# FusionBrain (Kandinsky) API настройки
FUSIONBRAIN_API_KEY = os.getenv('FUSIONBRAIN_API_KEY')
FUSIONBRAIN_SECRET_KEY = os.getenv('FUSIONBRAIN_SECRET_KEY')
FUSIONBRAIN_EMAIL = os.getenv('FUSIONBRAIN_EMAIL')
FUSIONBRAIN_PASSWORD = os.getenv('FUSIONBRAIN_PASSWORD')

# Инициализация Kandinsky модели
kandinsky_model = None
if KANDINSKY_AVAILABLE:
    try:
        # Приоритет: сначала пробуем api_key/secret_key, потом email/password
        if FUSIONBRAIN_API_KEY and FUSIONBRAIN_SECRET_KEY:
            kandinsky_model = FusionBrainApi(ApiApi(FUSIONBRAIN_API_KEY, FUSIONBRAIN_SECRET_KEY))
            logger.info("Kandinsky модель инициализирована через API ключи")
        elif FUSIONBRAIN_EMAIL and FUSIONBRAIN_PASSWORD:
            kandinsky_model = FusionBrainApi(ApiWeb(FUSIONBRAIN_EMAIL, FUSIONBRAIN_PASSWORD))
            logger.info("Kandinsky модель инициализирована через email/password")
        else:
            logger.warning("FUSIONBRAIN_API_KEY/SECRET_KEY или FUSIONBRAIN_EMAIL/PASSWORD не найдены. Генерация изображений через Kandinsky будет недоступна.")
    except Exception as e:
        kandinsky_model = None
        logger.error(f"Ошибка инициализации Kandinsky модели: {e}")
else:
    logger.warning("AsyncKandinsky не установлен. Установите: pip install AsyncKandinsky")

# Путь к папке TelegramBot (теперь в backend/telegram_bot)
# Проверяем оба возможных пути: в Docker (/app) и локально
possible_paths = [
    os.path.join(BASE_DIR, "backend", "telegram_bot"),  # Локальная разработка
    os.path.join("/app", "backend", "telegram_bot"),     # Docker
    os.path.join(BASE_DIR, "telegram_bot"),              # Альтернативный путь
]

TELEGRAM_BOT_DIR = None
for path in possible_paths:
    if os.path.exists(path):
        TELEGRAM_BOT_DIR = path
        break

# Если ни один путь не найден, используем путь в /app для Docker
if not TELEGRAM_BOT_DIR:
    TELEGRAM_BOT_DIR = os.path.join("/app", "backend", "telegram_bot")
    # Пытаемся создать директорию, если её нет
    try:
        os.makedirs(TELEGRAM_BOT_DIR, exist_ok=True)
        logger.info(f"Создана папка: {TELEGRAM_BOT_DIR}")
    except Exception as e:
        logger.warning(f"Не удалось создать папку {TELEGRAM_BOT_DIR}: {e}")

CHANNELS_FILE = os.path.join(TELEGRAM_BOT_DIR, "channels.json")
AUTH_TOKENS_FILE = os.path.join(TELEGRAM_BOT_DIR, "auth_tokens.json")

logger.info(f"Используется папка Telegram Bot: {TELEGRAM_BOT_DIR}")
logger.info(f"Файл каналов: {CHANNELS_FILE} (существует: {os.path.exists(CHANNELS_FILE)})")

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.warning(f"BOT_TOKEN не найден. Проверьте файл: {env_path}")
    logger.warning("Функция отправки статей в Telegram будет недоступна.")
    logger.warning("Для включения добавьте BOT_TOKEN в .env файл.")

# OpenRouter API настройки (для Qwen)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_API_URL = os.getenv('OPENROUTER_API_URL', 'https://openrouter.ai/api/v1/chat/completions')
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'qwen/qwen2.5-72b-instruct')  # По умолчанию используем Qwen

# YandexGPT API настройки
YANDEX_CLOUD_API_KEY = os.getenv('YANDEX_CLOUD_API_KEY')
YANDEX_CLOUD_PROJECT = os.getenv('YANDEX_CLOUD_PROJECT', 'b1goig30m707ojip72c7')
YANDEX_CLOUD_ASSISTANT_ID = os.getenv('YANDEX_CLOUD_ASSISTANT_ID', 'fvtfdp5dm8r044bnumjl')

# Инициализация YandexGPT клиента
yandex_client = None
yandex_default_headers = {}
if YANDEX_CLOUD_API_KEY and OPENAI_AVAILABLE:
    try:
        # Временно отключаем переменные окружения для proxies, если они есть
        import os
        old_http_proxy = os.environ.pop('HTTP_PROXY', None)
        old_https_proxy = os.environ.pop('HTTPS_PROXY', None)
        old_http_proxy_lower = os.environ.pop('http_proxy', None)
        old_https_proxy_lower = os.environ.pop('https_proxy', None)
        
        try:
            # Инициализируем клиент
            yandex_client = OpenAI(
                api_key=YANDEX_CLOUD_API_KEY,
                base_url="https://rest-assistant.api.cloud.yandex.net/v1"
            )
            
            # Добавляем project в заголовки по умолчанию
            yandex_default_headers = {
                "x-folder-id": YANDEX_CLOUD_PROJECT
            }
            logger.info("✅ YandexGPT API клиент инициализирован")
            logger.info(f"YandexGPT API Key: {YANDEX_CLOUD_API_KEY[:10]}...")
            logger.info(f"YandexGPT Project: {YANDEX_CLOUD_PROJECT}")
        finally:
            # Восстанавливаем переменные окружения, если они были
            if old_http_proxy:
                os.environ['HTTP_PROXY'] = old_http_proxy
            if old_https_proxy:
                os.environ['HTTPS_PROXY'] = old_https_proxy
            if old_http_proxy_lower:
                os.environ['http_proxy'] = old_http_proxy_lower
            if old_https_proxy_lower:
                os.environ['https_proxy'] = old_https_proxy_lower
    except Exception as e:
        yandex_client = None
        logger.error(f"❌ Ошибка инициализации YandexGPT API: {e}")
        logger.error(f"Тип ошибки: {type(e).__name__}")
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")
elif not OPENAI_AVAILABLE:
    logger.warning("OpenAI библиотека не установлена. YandexGPT будет недоступен. Установите: pip install openai")
elif not YANDEX_CLOUD_API_KEY:
    logger.warning("YANDEX_CLOUD_API_KEY не найден. YandexGPT будет недоступен.")

if BOT_TOKEN:
    logger.info("BOT_TOKEN успешно загружен")
    logger.info(f"Используется файл каналов: {CHANNELS_FILE}")
else:
    logger.info("BOT_TOKEN не установлен. Telegram функции отключены.")
if OPENROUTER_API_KEY:
    logger.info("OpenRouter API (Qwen) настроен")
    logger.info(f"OpenRouter модель: {OPENROUTER_MODEL}")
    logger.info(f"OpenRouter URL: {OPENROUTER_API_URL}")
else:
    logger.warning("OpenRouter API не настроен. Добавьте OPENROUTER_API_KEY в .env")

# Инициализация базы данных
try:
    from database import init_db, get_or_create_user, save_user_url, save_processing_result
    if init_db():
        logger.info("✅ База данных подключена")
        DB_AVAILABLE = True
    else:
        logger.warning("⚠️ База данных недоступна. Функции сохранения данных отключены.")
        DB_AVAILABLE = False
except ImportError as e:
    logger.warning(f"⚠️ Модуль database не найден: {e}. Функции сохранения данных отключены.")
    DB_AVAILABLE = False
except Exception as e:
    logger.warning(f"⚠️ Ошибка инициализации БД: {e}. Функции сохранения данных отключены.")
    DB_AVAILABLE = False

# Предупреждение о недоступности aiogram
if not AIOGRAM_AVAILABLE:
    logger.warning("aiogram не установлен. Функция отправки статей будет недоступна.")

# Bot будет создаваться для каждого запроса, чтобы избежать проблем с сессией
logger.info("Aiogram Bot готов к использованию")


def load_channels():
    """Загружает список каналов из файла"""
    if os.path.exists(CHANNELS_FILE):
        try:
            with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('channels', [])
        except Exception as e:
            logger.error(f"Ошибка загрузки каналов: {e}")
            return []
    return []


# Хранилище токенов авторизации
auth_tokens = {}

def load_auth_tokens():
    """Загружает токены из файла"""
    global auth_tokens
    if os.path.exists(AUTH_TOKENS_FILE):
        try:
            with open(AUTH_TOKENS_FILE, 'r', encoding='utf-8') as f:
                loaded_tokens = json.load(f)
                # Удаляем только истекшие pending токены (неиспользованные)
                # Авторизованные токены не удаляем - они бессрочные
                current_time = time.time()
                auth_tokens = {
                    k: v for k, v in loaded_tokens.items()
                    if v.get('status') == 'authorized' or v.get('expires_at', 0) > current_time
                }
                logger.info(f"Загружено активных токенов: {len(auth_tokens)}")
        except json.JSONDecodeError:
            logger.warning("Файл токенов поврежден, создаю новый")
            auth_tokens = {}
        except Exception as e:
            logger.error(f"Ошибка загрузки токенов: {e}")
            auth_tokens = {}
    else:
        auth_tokens = {}


def save_auth_tokens():
    """Сохраняет токены в файл"""
    try:
        os.makedirs(os.path.dirname(AUTH_TOKENS_FILE), exist_ok=True)
        with open(AUTH_TOKENS_FILE, 'w', encoding='utf-8') as f:
            json.dump(auth_tokens, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения токенов: {e}")


def generate_auth_token():
    """Генерирует новый токен авторизации (бессрочный)"""
    global auth_tokens
    load_auth_tokens()
    
    token = secrets.token_urlsafe(32)
    # Устанавливаем очень большое время жизни (10 лет) - токен действителен пока пользователь авторизован
    expires_at = time.time() + (10 * 365 * 24 * 60 * 60)  # 10 лет
    auth_tokens[token] = {
        'expires_at': expires_at,
        'status': 'pending',  # pending, authorized, expired
        'user_data': None
    }
    save_auth_tokens()
    logger.info(f"Сгенерирован новый токен (бессрочный): {token[:10]}...")
    return token


def verify_auth_token(token):
    """Проверяет токен и возвращает данные пользователя (бессрочный для авторизованных)"""
    load_auth_tokens()
    
    if token not in auth_tokens:
        return None
    
    token_data = auth_tokens[token]
    
    # Проверяем статус - для авторизованных токенов не проверяем срок действия
    if token_data['status'] != 'authorized':
        return None
    
    # Для авторизованных токенов не проверяем срок действия - они бессрочные
    # Только для pending токенов проверяем срок (чтобы удалить неиспользованные)
    if token_data['status'] == 'pending' and token_data['expires_at'] < time.time():
        del auth_tokens[token]
        save_auth_tokens()
        return None
    
    return token_data.get('user_data')


def authorize_token(token, user_data):
    """Авторизует токен с данными пользователя (делает токен бессрочным)"""
    global auth_tokens
    load_auth_tokens()
    
    if token not in auth_tokens:
        return False
    
    auth_tokens[token]['status'] = 'authorized'
    auth_tokens[token]['user_data'] = user_data
    auth_tokens[token]['authorized_at'] = time.time()
    # Устанавливаем очень большое время жизни для авторизованного токена (бессрочный)
    auth_tokens[token]['expires_at'] = time.time() + (10 * 365 * 24 * 60 * 60)  # 10 лет
    save_auth_tokens()
    logger.info(f"Токен {token[:10]}... успешно авторизован (бессрочный)")
    return True


# Загружаем токены при старте
load_auth_tokens()


def clean_model_response(text):
    """Очищает ответ модели от мыслей, комментариев и лишних фраз"""
    if not text:
        return ""
    
    original_text = text
    text = text.strip()
    
    # Удаляем теги reasoning (включая содержимое между ними)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<reasoning>.*?</reasoning>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Удаляем оставшиеся одиночные теги
    text = re.sub(r'</?redacted_reasoning>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</?reasoning>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</?thinking>', '', text, flags=re.IGNORECASE)
    
    # Удаляем распространённые предисловия (регистронезависимо)
    prefixes_to_remove = [
        r"^вот переписанный текст:?\s*",
        r"^переписанный текст:?\s*",
        r"^вот вариант:?\s*",
        r"^вот переписанный вариант:?\s*",
        r"^переписанный вариант:?\s*",
        r"^вот текст:?\s*",
        r"^текст в стиле:?\s*",
        r"^думаю:?\s*",
        r"^я думаю:?\s*",
        r"^можно переписать так:?\s*",
        r"^переписанный вариант текста:?\s*",
        r"^вот как можно переписать:?\s*",
        r"^вот переписанный:?\s*",
        r"^переписанный:?\s*",
        r"^вот:?\s*",
        r"^think:?\s*",
        r"^thinking:?\s*",
        r"^я думаю,?\s*",
        r"^думаю,?\s*",
    ]
    
    for prefix in prefixes_to_remove:
        text = re.sub(prefix, '', text, flags=re.IGNORECASE).strip()
    
    # Удаляем мысли в скобках
    text = re.sub(r'\([^)]*(?:думаю|я думаю|можно|вариант|переписанный|think|thinking)[^)]*\)', '', text, flags=re.IGNORECASE)
    
    # Удаляем кавычки в начале и конце, если они есть
    text = re.sub(r'^["\'«»]|["\'«»]$', '', text).strip()
    
    # Удаляем строки, которые выглядят как мысли
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Пропускаем строки, которые явно являются мыслями
        thought_patterns = [
            r'^(думаю|я думаю|можно|вариант|переписанный|вот|это|так|например|то есть|think|thinking)',
            r'^\(.*(думаю|можно|вариант).*\)$'
        ]
        
        is_thought = False
        for pattern in thought_patterns:
            if re.match(pattern, line, re.IGNORECASE) and len(line) < 150:
                is_thought = True
                break
        
        if not is_thought:
            cleaned_lines.append(line)
    
    result = '\n'.join(cleaned_lines).strip()
    
    # Если после очистки осталось слишком мало текста, возвращаем оригинал
    if len(result) < 20:
        return original_text.strip()
    
    return result


def extract_text_from_url(url):
    """Извлекает текст статьи из URL (улучшенная версия)"""
    try:
        # Используем более полные заголовки для обхода защиты от ботов
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        # Используем сессию для сохранения cookies
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(url, timeout=30, allow_redirects=True)
        
        # Обрабатываем ошибки 403 более корректно
        if response.status_code == 403:
            logger.warning(f"Получен 403 Forbidden для {url}, пробуем с другими заголовками...")
            # Пробуем с другим User-Agent
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
            headers['Referer'] = 'https://www.google.com/'
            session.headers.update(headers)
            response = session.get(url, timeout=30, allow_redirects=True)
            
            if response.status_code == 403:
                error_msg = f"Сайт {url} блокирует доступ (403 Forbidden). Возможно, требуется авторизация или сайт защищен от автоматических запросов."
                logger.error(error_msg)
                raise requests.exceptions.HTTPError(error_msg, response=response)
        
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Удаляем скрипты и стили
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        # Извлекаем текст из основных тегов
        text_parts = []
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'article', 'div']):
            text = tag.get_text(strip=True)
            if text and len(text) > 20:  # Игнорируем короткие фрагменты
                text_parts.append(text)
        
        article_text = '\n\n'.join(text_parts)
        
        if not article_text or len(article_text) < 100:
            # Если не удалось извлечь текст, пробуем получить весь текст страницы
            article_text = soup.get_text(separator='\n', strip=True)
        
        # Очищаем текст от нежелательных фраз (реклама, регистрация и т.д.)
        unwanted_phrases = [
            r'\*\*OMG[^\*]*\*\*',  # **OMG, это реально!**
            r'🚨\s*\*\*[^\*]*Регистрация пройдена успешно[^\*]*\*\*\s*🚨',  # 🚨 **Регистрация пройдена успешно!** 🚨
            r'Перейти по ссылке из письма[^\.]*\.',  # Перейти по ссылке из письма...
            r'если не видите[^\.]*\.',  # если не видите, ищите в спаме
            r'ищите в спаме',
            r'---\s*###\s*📅',  # --- ### 📅
            r'Регистрация пройдена успешно[!\.]*',
            r'Пожалуйста[^\.]*перейдите[^\.]*\.',
            r'Перейдите по ссылке[^\.]*\.',
        ]
        
        for pattern in unwanted_phrases:
            article_text = re.sub(pattern, '', article_text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Убираем лишние пробелы после очистки
        article_text = re.sub(r'\s+', ' ', article_text)
        article_text = re.sub(r'\n\s*\n', '\n\n', article_text)
        article_text = article_text.strip()
        
        return article_text[:50000]  # Ограничиваем длину
    except Exception as e:
        logger.error(f"Ошибка извлечения текста из URL {url}: {e}")
        raise


def extract_article_text(url):
    """Извлекает текст статьи из URL (совместимость)"""
    return extract_text_from_url(url)


def extract_image_from_url(url):
    """Извлекает изображение из статьи (og:image, article:image, или первое крупное изображение)"""
    try:
        # Используем те же заголовки, что и для извлечения текста
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url, timeout=30, allow_redirects=True)
        
        # Обрабатываем ошибки 403
        if response.status_code == 403:
            logger.warning(f"Получен 403 Forbidden при извлечении изображения из {url}, пробуем с другими заголовками...")
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
            headers['Referer'] = 'https://www.google.com/'
            session.headers.update(headers)
            response = session.get(url, timeout=30, allow_redirects=True)
        
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Приоритет 1: Open Graph изображение
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            image_url = og_image.get('content')
            # Если относительный URL, делаем абсолютным
            if image_url.startswith('//'):
                image_url = 'https:' + image_url
            elif image_url.startswith('/'):
                image_url = urljoin(url, image_url)
            logger.info(f"Найдено og:image: {image_url}")
            return image_url
        
        # Приоритет 2: article:image
        article_image = soup.find('meta', property='article:image')
        if article_image and article_image.get('content'):
            image_url = article_image.get('content')
            if image_url.startswith('//'):
                image_url = 'https:' + image_url
            elif image_url.startswith('/'):
                image_url = urljoin(url, image_url)
            logger.info(f"Найдено article:image: {image_url}")
            return image_url
        
        # Приоритет 3: Первое крупное изображение в статье
        images = soup.find_all('img')
        for img in images:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if not src:
                continue
            
            # Пропускаем маленькие изображения (иконки, логотипы)
            width = img.get('width')
            height = img.get('height')
            if width and height:
                try:
                    if int(width) < 200 or int(height) < 200:
                        continue
                except (ValueError, TypeError):
                    pass
            
            # Пропускаем логотипы и иконки по классам/alt
            img_class = img.get('class', [])
            img_alt = (img.get('alt') or '').lower()
            if any(skip in str(img_class).lower() or skip in img_alt for skip in ['logo', 'icon', 'avatar', 'button']):
                continue
            
            # Делаем URL абсолютным
            if src.startswith('//'):
                image_url = 'https:' + src
            elif src.startswith('/'):
                image_url = urljoin(url, src)
            elif not src.startswith('http'):
                image_url = urljoin(url, src)
            else:
                image_url = src
            
            logger.info(f"Найдено изображение в статье: {image_url}")
            return image_url
        
        logger.warning(f"Изображение не найдено в статье: {url}")
        return None
    except Exception as e:
        logger.error(f"Ошибка извлечения изображения из URL {url}: {e}")
        return None


def extract_keywords_for_image_search(article_text, rewritten_text=None):
    """Извлекает ключевые слова из статьи для поиска изображения"""
    # Сначала убираем HTML теги из текста
    def clean_html(text):
        """Убирает HTML теги из текста"""
        if not text:
            return ""
        # Убираем все HTML теги (включая самозакрывающиеся и с атрибутами)
        text = re.sub(r'<[^>]+>', '', text)
        # Убираем HTML комментарии
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        # Заменяем HTML entities (включая числовые)
        try:
            text = html_module.unescape(text)
        except:
            # Если html.unescape не работает, делаем вручную
            text = text.replace('&nbsp;', ' ')
            text = text.replace('&amp;', '&')
            text = text.replace('&lt;', '<')
            text = text.replace('&gt;', '>')
            text = text.replace('&quot;', '"')
            text = text.replace('&#39;', "'")
            text = text.replace('&apos;', "'")
            # Убираем числовые entities
            text = re.sub(r'&#\d+;', '', text)
            text = re.sub(r'&#x[0-9a-fA-F]+;', '', text)
        # Убираем оставшиеся HTML-подобные конструкции
        text = re.sub(r'&[a-zA-Z]+;', '', text)
        # Убираем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text)
        # Убираем слова, которые могут быть остатками HTML (html, div, span, p, br и т.д.)
        html_words = ['html', 'div', 'span', 'p', 'br', 'img', 'src', 'alt', 'class', 'id', 'style', 'href', 'link']
        words = text.split()
        words = [w for w in words if w.lower() not in html_words]
        text = ' '.join(words)
        text = text.strip()
        return text
    
    # Очищаем текст от HTML
    article_text = clean_html(article_text)
    if rewritten_text:
        rewritten_text = clean_html(rewritten_text)
    
    # Служебные слова, которые нужно пропускать
    stop_words = {
        'регистрация', 'пройдена', 'успешно', 'пожалуйста', 'перейдите', 'нажмите',
        'вход', 'войти', 'выход', 'выйти', 'далее', 'продолжить', 'отмена',
        'это', 'этот', 'эта', 'эти', 'такой', 'такая', 'такие',
        'быть', 'есть', 'был', 'была', 'было', 'были',
        'и', 'в', 'на', 'с', 'по', 'для', 'из', 'от', 'к', 'о', 'об', 'со', 'во',
        'как', 'что', 'где', 'когда', 'кто', 'куда', 'откуда',
        'не', 'нет', 'ни', 'без', 'про', 'при', 'над', 'под', 'за', 'перед'
    }
    
    # Пробуем извлечь заголовок (первая строка или строка с заглавными буквами)
    lines = article_text.split('\n')
    title_candidates = []
    
    for line in lines[:5]:  # Проверяем первые 5 строк
        line = line.strip()
        if len(line) > 10 and len(line) < 200:  # Разумная длина для заголовка
            # Если строка содержит много заглавных букв или короткая - вероятно заголовок
            if line[0].isupper() or len(line.split()) <= 10:
                title_candidates.append(line)
    
    # Используем первый подходящий заголовок или начало статьи
    text_to_analyze = title_candidates[0] if title_candidates else article_text
    
    # Если есть переписанный текст, используем его (он более структурирован)
    if rewritten_text:
        rewritten_lines = rewritten_text.split('\n')
        for line in rewritten_lines[:3]:
            line = line.strip()
            if len(line) > 10 and len(line) < 200:
                if line[0].isupper() or '**' in line:  # Markdown заголовки
                    text_to_analyze = line
                    break
    
    # Убираем markdown разметку и спецсимволы
    text_to_analyze = re.sub(r'\*\*|\*|#|`|\[|\]|\(|\)', '', text_to_analyze)
    text_to_analyze = re.sub(r'[^\w\s]', ' ', text_to_analyze)
    
    # Убираем HTML/технические слова из текста для анализа
    html_tech_words = {'html', 'div', 'span', 'p', 'br', 'img', 'src', 'alt', 'class', 'id', 'style', 'href', 'link', 'http', 'https', 'www', 'com', 'ru', 'org', 'net'}
    words = text_to_analyze.split()
    words = [w for w in words if w.lower() not in html_tech_words and len(w) > 2]
    text_to_analyze = ' '.join(words)
    
    # Разбиваем на слова и фильтруем
    words = text_to_analyze.split()
    keywords = []
    
    for word in words:
        word_lower = word.lower().strip()
        # Пропускаем служебные слова, короткие слова, числа и HTML/технические слова
        if (len(word_lower) > 3 and 
            word_lower not in stop_words and 
            word_lower not in html_tech_words and
            not word_lower.isdigit() and
            word_lower.isalpha()):
            keywords.append(word_lower)
            if len(keywords) >= 5:  # Берем первые 5 ключевых слов
                break
    
    # Если не нашли ключевых слов, берем первые существительные из статьи
    if len(keywords) < 3:
        all_words = article_text.split()
        for word in all_words:
            word_lower = word.lower().strip()
            word_clean = re.sub(r'[^\w]', '', word_lower)
            if (len(word_clean) > 4 and 
                word_clean not in stop_words and 
                word_clean not in html_tech_words and
                word_clean.isalpha()):
                keywords.append(word_clean)
                if len(keywords) >= 5:
                    break
    
    # Если все еще нет ключевых слов, используем первые слова статьи
    if len(keywords) < 2:
        words = article_text.split()[:10]
        for word in words:
            word_clean = re.sub(r'[^\w]', '', word.lower().strip())
            if (len(word_clean) > 3 and 
                word_clean.isalpha() and 
                word_clean not in html_tech_words and
                word_clean not in stop_words):
                keywords.append(word_clean)
                if len(keywords) >= 3:
                    break
    
    result = ' '.join(keywords[:5])  # Максимум 5 ключевых слов
    return result if result else 'news article'  # Fallback


def search_image_from_pexels(query, api_key=None):
    """Ищет изображение через Pexels API"""
    if not api_key:
        api_key = os.getenv('PEXELS_API_KEY')
    
    if not api_key:
        logger.warning("PEXELS_API_KEY не настроен, пропускаем поиск через Pexels")
        return None
    
    try:
        # Используем весь запрос (уже обработанный функцией extract_keywords_for_image_search)
        # Ограничиваем до 5 слов для лучших результатов
        keywords = query.split()[:5]
        search_query = ' '.join(keywords)
        
        logger.info(f"Поиск в Pexels по запросу: {search_query}")
        
        headers = {
            'Authorization': api_key
        }
        params = {
            'query': search_query,
            'per_page': 1,
            'orientation': 'landscape'
        }
        
        response = requests.get('https://api.pexels.com/v1/search', headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get('photos') and len(data['photos']) > 0:
            photo = data['photos'][0]
            image_url = photo.get('src', {}).get('large') or photo.get('src', {}).get('original')
            logger.info(f"Найдено изображение через Pexels: {image_url}")
            return image_url
        
        logger.warning(f"Изображение не найдено через Pexels для запроса: {search_query}")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"Ошибка подключения к Pexels API (проблема сети/DNS): {e}")
        return None
    except requests.exceptions.Timeout as e:
        logger.warning(f"Таймаут при подключении к Pexels API: {e}")
        return None
    except Exception as e:
        logger.error(f"Ошибка поиска изображения через Pexels: {e}")
        return None


def search_image_from_unsplash(query):
    """Ищет изображение через Unsplash Source API (бесплатный вариант без ключа)"""
    try:
        # Используем весь запрос (уже обработанный функцией extract_keywords_for_image_search)
        # Ограничиваем до 5 слов
        keywords = query.split()[:5]
        search_query = ' '.join(keywords)
        
        # Unsplash Source API - генерирует случайное изображение по ключевым словам
        # Формат: https://source.unsplash.com/1600x900/?keyword1,keyword2
        # Убираем спецсимволы и оставляем только буквы и цифры
        clean_query = re.sub(r'[^a-zA-Zа-яА-Я0-9\s]', '', search_query)
        search_terms = clean_query.replace(' ', ',').lower()[:50]  # Ограничиваем длину
        
        if not search_terms:
            logger.warning("Не удалось извлечь ключевые слова для Unsplash")
            return None
        
        url = f"https://source.unsplash.com/1600x900/?{search_terms}"
        
        # Проверяем, что URL доступен (HEAD запрос для проверки)
        response = requests.head(url, timeout=15, allow_redirects=True)
        final_url = response.url if hasattr(response, 'url') else url
        
        # Если получили редирект на изображение, значит оно доступно
        if response.status_code in [200, 301, 302] and ('unsplash' in final_url or 'images.unsplash.com' in final_url):
            logger.info(f"Найдено изображение через Unsplash: {final_url}")
            return final_url
        
        return None
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"Ошибка подключения к Unsplash (проблема сети/DNS): {e}")
        return None
    except requests.exceptions.Timeout as e:
        logger.warning(f"Таймаут при подключении к Unsplash: {e}")
        return None
    except Exception as e:
        logger.error(f"Ошибка поиска изображения через Unsplash: {e}")
        return None


def generate_image_with_kandinsky_direct(prompt, style=None):
    """Генерация изображения через официальный FusionBrain API (согласно документации)"""
    if not FUSIONBRAIN_API_KEY or not FUSIONBRAIN_SECRET_KEY:
        logger.warning("FUSIONBRAIN_API_KEY или FUSIONBRAIN_SECRET_KEY не настроены, пропускаем генерацию")
        return None
    
    try:
        import base64
        import uuid
        
        # Упрощаем промпт для генерации (первые 30 слов для лучшего качества)
        # Убираем HTML теги из промпта
        clean_prompt = re.sub(r'<[^>]+>', '', prompt)  # Убираем все HTML теги
        clean_prompt = re.sub(r'\s+', ' ', clean_prompt).strip()  # Убираем лишние пробелы
        simple_prompt = ' '.join(clean_prompt.split()[:30])
        
        # Формируем промпт для генерации изображения
        image_prompt = f"Изображение на тему: {simple_prompt}"
        
        # Ограничиваем длину промпта до 1000 символов (согласно документации)
        if len(image_prompt) > 1000:
            image_prompt = image_prompt[:1000]
        
        logger.info(f"Попытка генерации изображения через Kandinsky API с промптом: {image_prompt[:50]}...")
        
        # Настройки API согласно документации
        API_URL = 'https://api-key.fusionbrain.ai/'
        AUTH_HEADERS = {
            'X-Key': f'Key {FUSIONBRAIN_API_KEY}',
            'X-Secret': f'Secret {FUSIONBRAIN_SECRET_KEY}',
        }
        
        # Шаг 1: Получаем pipeline_id
        logger.info("Получение pipeline_id...")
        response = requests.get(API_URL + 'key/api/v1/pipelines', headers=AUTH_HEADERS, timeout=30)
        response.raise_for_status()
        pipelines = response.json()
        
        if not pipelines or len(pipelines) == 0:
            logger.error("Не найдено доступных pipelines")
            return None
        
        pipeline_id = pipelines[0]['id']
        logger.info(f"Получен pipeline_id: {pipeline_id}")
        
        # Шаг 2: Отправляем запрос на генерацию
        params = {
            "type": "GENERATE",
            "numImages": 1,
            "width": 1024,
            "height": 1024,
            "generateParams": {
                "query": image_prompt
            }
        }
        
        # Добавляем стиль, если указан
        if style and style != "DEFAULT":
            params["style"] = style
        
        data = {
            'pipeline_id': (None, pipeline_id),
            'params': (None, json.dumps(params, ensure_ascii=False), 'application/json')
        }
        
        logger.info("Отправка запроса на генерацию изображения...")
        response = requests.post(
            API_URL + 'key/api/v1/pipeline/run',
            headers=AUTH_HEADERS,
            files=data,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
        # Проверяем, не вернул ли сервис статус недоступности
        if 'pipeline_status' in result:
            logger.warning(f"Сервис недоступен: {result['pipeline_status']}")
            return None
        
        request_uuid = result.get('uuid')
        if not request_uuid:
            logger.error(f"Не получен UUID для запроса. Ответ: {result}")
            return None
        
        logger.info(f"Запрос на генерацию отправлен, UUID: {request_uuid}")
        
        # Шаг 3: Проверяем статус генерации
        max_attempts = 20  # Максимум 20 попыток
        delay = 5  # Задержка 5 секунд между попытками
        
        for attempt in range(max_attempts):
            time.sleep(delay)
            logger.info(f"Проверка статуса генерации (попытка {attempt + 1}/{max_attempts})...")
            
            response = requests.get(
                API_URL + f'key/api/v1/pipeline/status/{request_uuid}',
                headers=AUTH_HEADERS,
                timeout=30
            )
            response.raise_for_status()
            status_data = response.json()
            
            status = status_data.get('status')
            
            if status == 'DONE':
                # Генерация завершена
                result_data = status_data.get('result', {})
                files = result_data.get('files', [])
                
                if not files or len(files) == 0:
                    logger.warning("Генерация завершена, но файлы не получены")
                    return None
                
                # Декодируем Base64 изображение
                image_base64 = files[0]
                image_data = base64.b64decode(image_base64)
                
                # Сохраняем изображение
                uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
                if not os.path.exists(uploads_dir):
                    os.makedirs(uploads_dir)
                    logger.info(f"Создана папка для загрузок: {uploads_dir}")
                
                filename = f"kandinsky_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}.png"
                filepath = os.path.join(uploads_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
                port = os.getenv('PORT', '5000')
                image_url = f"http://localhost:{port}/uploads/{filename}"
                
                logger.info(f"Изображение успешно сгенерировано и сохранено: {filepath}")
                return image_url
                
            elif status == 'FAIL':
                error_desc = status_data.get('errorDescription', 'Неизвестная ошибка')
                logger.error(f"Генерация не удалась: {error_desc}")
                return None
                
            elif status in ['INITIAL', 'PROCESSING']:
                # Продолжаем ждать
                continue
            else:
                logger.warning(f"Неизвестный статус: {status}")
        
        logger.error(f"Генерация превысила максимальное время ожидания ({max_attempts * delay} секунд)")
        return None
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP ошибка при генерации изображения: {e}")
        if e.response:
            logger.error(f"Ответ сервера: {e.response.text[:500]}")
        return None
    except Exception as e:
        logger.error(f"Ошибка генерации изображения через Kandinsky API: {e}", exc_info=True)
        return None


def generate_image_with_kandinsky(prompt, api_key=None, project_id=None):
    """Генерирует изображение через официальный FusionBrain API"""
    # Используем прямое обращение к API согласно документации
    return generate_image_with_kandinsky_direct(prompt)


def convert_markdown_to_html(text):
    """Конвертирует markdown в HTML, убирая синтаксис, но сохраняя структуру"""
    # Сначала убираем markdown синтаксис из текста
    # Убираем markdown заголовки (# ## ### и т.д.)
    text = re.sub(r'^#{1,6}\s+(.+)$', r'\1', text, flags=re.MULTILINE)
    
    # Убираем жирный текст (**текст** или __текст__)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    
    # Убираем курсив (*текст* или _текст_) - более аккуратно
    text = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'\1', text)
    text = re.sub(r'(?<!_)_([^_\n]+?)_(?!_)', r'\1', text)
    
    # Убираем зачеркнутый текст (~~текст~~)
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    
    # Убираем inline код (`код`)
    text = re.sub(r'`([^`]+?)`', r'\1', text)
    
    # Экранируем HTML для безопасности
    text = html_module.escape(text)
    
    # Обрабатываем списки и абзацы
    lines = text.split('\n')
    result_lines = []
    in_ul = False
    in_ol = False
    
    for line in lines:
        stripped = line.strip()
        
        # Маркированный список (-, *, +)
        ul_match = re.match(r'^[\s]*[-*+]\s+(.+)$', line)
        # Нумерованный список (1., 2., и т.д.)
        ol_match = re.match(r'^[\s]*\d+\.\s+(.+)$', line)
        
        if ul_match:
            if in_ol:
                result_lines.append('</ol>')
                in_ol = False
            if not in_ul:
                result_lines.append('<ul>')
                in_ul = True
            content = ul_match.group(1).strip()
            result_lines.append(f'<li>{content}</li>')
        elif ol_match:
            if in_ul:
                result_lines.append('</ul>')
                in_ul = False
            if not in_ol:
                result_lines.append('<ol>')
                in_ol = True
            content = ol_match.group(1).strip()
            result_lines.append(f'<li>{content}</li>')
        else:
            # Закрываем списки при переходе к обычному тексту
            if in_ul:
                result_lines.append('</ul>')
                in_ul = False
            if in_ol:
                result_lines.append('</ol>')
                in_ol = False
            
            if stripped:
                result_lines.append(f'<p>{stripped}</p>')
            # Пустые строки не добавляем (они создают лишние разрывы)
    
    # Закрываем списки, если они остались открытыми
    if in_ul:
        result_lines.append('</ul>')
    if in_ol:
        result_lines.append('</ol>')
    
    # Объединяем все строки
    result = '\n'.join(result_lines)
    
    # Убираем пустые параграфы
    result = re.sub(r'<p>\s*</p>', '', result)
    
    # Убираем множественные пустые параграфы
    result = re.sub(r'(</p>\s*<p>){2,}', '</p><p>', result)
    
    return result


def rewrite_article_with_ml(article_text, model_type):
    """Рерайтит статью через ML Service (RUT5 или FLAN-T5)"""
    ML_SERVICE_URL = os.getenv('ML_SERVICE_URL', 'http://localhost:8000')
    API_KEY = os.getenv('API_KEY', 'your-api-key-here')
    
    # RUT5 работает с небольшими фрагментами текста
    # Разбиваем длинный текст на предложения и обрабатываем частями
    import re
    
    # Разбиваем текст на предложения (разделители: . ! ?)
    sentences = re.split(r'([.!?]\s+)', article_text)
    # Объединяем разделители с предложениями
    text_parts = []
    for i in range(0, len(sentences), 2):
        if i + 1 < len(sentences):
            text_parts.append(sentences[i] + sentences[i+1])
        elif sentences[i].strip():
            text_parts.append(sentences[i])
    
    # Обрабатываем частями (максимум 200 символов на запрос для RUT5)
    max_chunk_size = 200
    paraphrased_parts = []
    
    current_chunk = ""
    for part in text_parts:
        if len(current_chunk) + len(part) <= max_chunk_size:
            current_chunk += part
        else:
            if current_chunk.strip():
                paraphrased_parts.append(current_chunk)
            current_chunk = part
    
    # Добавляем последний chunk
    if current_chunk.strip():
        paraphrased_parts.append(current_chunk)
    
    # Если текст короткий, обрабатываем целиком
    if len(article_text) <= max_chunk_size:
        paraphrased_parts = [article_text]
    
    logger.info(f"Обработка текста через ML Service ({model_type}): {len(paraphrased_parts)} частей, общая длина: {len(article_text)}")
    
    try:
        all_paraphrased = []
        for i, chunk in enumerate(paraphrased_parts):
            logger.info(f"Обработка части {i+1}/{len(paraphrased_parts)} (длина: {len(chunk)} символов)...")
            try:
                response = requests.post(
                    f"{ML_SERVICE_URL}/api/v1/paraphrase",
                    json={
                        "text": chunk,
                        "max_length": 512,
                        "temperature": 0.7,
                        "top_p": 0.9
                    },
                    headers={
                        "Content-Type": "application/json",
                        "X-API-Key": API_KEY
                    },
                    timeout=300  # Увеличиваем таймаут до 5 минут для первой загрузки модели
                )
                
                if response.status_code == 200:
                    data = response.json()
                    paraphrased_chunk = data.get('paraphrased', chunk)
                    all_paraphrased.append(paraphrased_chunk)
                    logger.info(f"Часть {i+1}/{len(paraphrased_parts)} обработана успешно")
                else:
                    logger.error(f"Ошибка ML Service для части {i+1}: {response.status_code} - {response.text}")
                    # В случае ошибки используем оригинальный текст
                    all_paraphrased.append(chunk)
            except requests.exceptions.Timeout:
                logger.error(f"Таймаут при обработке части {i+1} через ML Service")
                # В случае таймаута используем оригинальный текст
                all_paraphrased.append(chunk)
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка подключения к ML Service для части {i+1}: {e}")
                # В случае ошибки используем оригинальный текст
                all_paraphrased.append(chunk)
        
        # Объединяем все части
        result = ' '.join(all_paraphrased)
        logger.info(f"Обработка завершена. Итоговая длина: {len(result)} символов")
        return result
        
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обработке через ML Service: {e}")
        raise ValueError(f"Ошибка обработки через ML Service: {str(e)}")


def rewrite_article_with_yandex(article_text, style):
    """Рерайтит статью через YandexGPT API"""
    if not yandex_client:
        raise ValueError("YandexGPT API не настроен. Добавьте YANDEX_CLOUD_API_KEY в .env")
    
    style_prompts = {
        'scientific': 'Перепиши статью в научно-деловом стиле, сохраняя основную информацию и факты. Ответ должен быть на русском языке.',
        'meme': 'Перепиши статью в мемном стиле, сделай её более развлекательной и юмористической. Ответ должен быть на русском языке.',
        'casual': 'Перепиши статью в повседневном стиле, сделай её более простой и понятной для широкой аудитории. Ответ должен быть на русском языке.'
    }
    
    prompt = style_prompts.get(style, style_prompts['casual'])
    full_prompt = f"{prompt}\n\nВАЖНО: Весь ответ должен быть на русском языке. Не используй английский язык.\n\nТекст статьи:\n{article_text}"
    
    try:
        # Ограничиваем длину текста
        max_text_length = 12000
        if len(article_text) > max_text_length:
            article_text = article_text[:max_text_length] + "..."
            full_prompt = f"{prompt}\n\nВАЖНО: Весь ответ должен быть на русском языке. Не используй английский язык.\n\nТекст статьи:\n{article_text}"
        
        # Передаем project через extra_headers
        response = yandex_client.responses.create(
            prompt={
                "id": YANDEX_CLOUD_ASSISTANT_ID,
            },
            input=full_prompt,
            extra_headers={
                "x-folder-id": YANDEX_CLOUD_PROJECT
            }
        )
        
        result_text = response.output_text
        
        # Очищаем результат от мыслей модели и лишних комментариев
        cleaned_text = clean_model_response(result_text)
        
        return cleaned_text
    except Exception as e:
        logger.error(f"Ошибка рерайта через YandexGPT: {e}")
        raise ValueError(f"Ошибка подключения к YandexGPT API: {str(e)}")


def rewrite_article_with_openrouter(article_text, style):
    """Рерайтит статью через OpenRouter API"""
    if not OPENROUTER_API_KEY:
        raise ValueError("OpenRouter API не настроен. Добавьте OPENROUTER_API_KEY в .env")
    
    # Маппинг стилей для промпта
    style_mapping = {
        'scientific': 'НАУЧНО-ДЕЛОВОЙ',
        'meme': 'МЕМНЫЙ',
        'casual': 'ПОВСЕДНЕВНЫЙ'
    }
    
    style_name = style_mapping.get(style, 'ПОВСЕДНЕВНЫЙ')
    
    # Ограничиваем длину текста
    max_text_length = 12000
    if len(article_text) > max_text_length:
        article_text = article_text[:max_text_length] + "..."
    
    # Формируем промпт пользователя
    full_prompt = f"Перепиши следующий текст в стиле {style_name}:\n\n{article_text}"
    
    try:
        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://phoenix-lab.com',  # Опционально, для отслеживания
            'X-Title': 'Phoenix Lab'  # Опционально, для отслеживания
        }
        
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": """Ты — инструмент для рерайта текстов. Твоя единственная задача — переписать предоставленный текст в указанном стиле БЕЗ МЫСЛЕЙ.

Доступные стили:
- НАУЧНО-ДЕЛОВОЙ: формально, объективно, научная терминология
- МЕМНЫЙ: интернет-мемы, эмодзи, сленг, сарказм
- ПОВСЕДНЕВНЫЙ: просто, естественно, разговорно

ПРАВИЛА:
1. Отвечай ТОЛЬКО переписанным текстом
2. НИКАКИХ объяснений, комментариев, предисловий
3. НИКАКИХ фраз типа "Вот текст:", "Переписанный вариант:", "Думаю:" и т.п.
4. НИКАКИХ мыслей, рассуждений, мета-комментариев
5. НИКАКИХ кавычек вокруг текста
6. Начинай сразу с переписанного текста
7. Сохраняй смысл оригинала
8. Длина примерно как у оригинала"""
                },
                {
                    "role": "user",
                    "content": full_prompt
                }
            ],
            "temperature": 0.5,
            "max_tokens": 4000,
            "top_p": 0.95,
            "stream": False,
            # Стоп-последовательности для остановки генерации при начале мыслей
            "stop": [
                "\nДумаю:",
                "\nВот переписанный текст:",
                "\nThink:",
                "\n("
            ]
        }
        
        logger.info(f"Отправка запроса в OpenRouter для стиля: {style}")
        logger.info(f"OpenRouter URL: {OPENROUTER_API_URL}")
        logger.info(f"OpenRouter Model: {OPENROUTER_MODEL}")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Ответ OpenRouter получен")
        
        # Обрабатываем ответ OpenRouter API (OpenAI-совместимый формат)
        if 'choices' in result and len(result['choices']) > 0:
            rewritten_text = result['choices'][0]['message']['content']
            
            # Очищаем ответ от мыслей модели и лишних комментариев
            cleaned_text = clean_model_response(rewritten_text)
            return cleaned_text
        else:
            logger.error(f"Неожиданный формат ответа: {result}")
            raise ValueError("Неожиданный формат ответа от OpenRouter API")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка HTTP запроса к OpenRouter: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                logger.error(f"Ответ сервера: {error_detail}")
            except:
                logger.error(f"Ответ сервера: {e.response.text}")
        raise ValueError(f"Ошибка подключения к OpenRouter API: {str(e)}")
    except Exception as e:
        logger.error(f"Ошибка рерайта через OpenRouter: {e}")
        raise


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Отдает загруженные файлы (изображения)"""
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    return send_from_directory(uploads_dir, filename)


@app.route('/api/rewrite-article', methods=['POST', 'OPTIONS'])
def rewrite_article():
    """Обрабатывает статью: получает текст по URL и рерайтит через выбранный провайдер"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Запрос должен содержать JSON данные'}), 400
        
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'Данные запроса не получены'}), 400
        
        article_url = data.get('url', '')
        article_text_direct = data.get('text', '')  # Прямой ввод текста
        style = data.get('style', 'casual')
        provider = data.get('provider', 'qwen')  # 'qwen', 'yandex', 'rut5', 'flant5'
        
        # Проверяем, передан ли URL или текст
        if not article_url and not article_text_direct:
            logger.error("URL или текст статьи не указан в запросе")
            return jsonify({'success': False, 'error': 'URL или текст статьи не указан'}), 400
        
        if article_url and article_text_direct:
            logger.error("Указаны и URL, и текст. Укажите только один вариант")
            return jsonify({'success': False, 'error': 'Указаны и URL, и текст. Укажите только один вариант'}), 400
        
        if style not in ['scientific', 'meme', 'casual']:
            logger.error(f"Неверный стиль рерайта: {style}")
            return jsonify({'success': False, 'error': 'Неверный стиль рерайта'}), 400
        
        if provider not in ['qwen', 'yandex', 'rut5', 'flant5']:
            logger.error(f"Неверный провайдер: {provider}")
            return jsonify({'success': False, 'error': 'Неверный провайдер. Используйте "qwen", "yandex", "rut5" или "flant5"'}), 400
        
        # Проверяем доступность провайдера
        if provider == 'qwen' and not OPENROUTER_API_KEY:
            return jsonify({'success': False, 'error': 'OpenRouter API не настроен. Добавьте OPENROUTER_API_KEY в .env'}), 400
        elif provider == 'yandex' and not yandex_client:
            return jsonify({'success': False, 'error': 'YandexGPT API не настроен. Добавьте YANDEX_CLOUD_API_KEY в .env'}), 400
        elif provider in ['rut5', 'flant5']:
            # ML модели не требуют дополнительных проверок, они работают через ML service
            pass
        
        # Определяем, используем ли мы URL или прямой текст
        if article_text_direct:
            # Используем прямой текст
            article_text = article_text_direct.strip()
            logger.info(f"Начало обработки статьи: прямой текст, длина={len(article_text)}, стиль={style}, провайдер={provider}")
        else:
            # Извлекаем текст из URL
            logger.info(f"Начало обработки статьи: URL={article_url}, стиль={style}, провайдер={provider}")
            logger.info(f"Извлечение текста из URL: {article_url}")
            try:
                article_text = extract_text_from_url(article_url)
                logger.info(f"Текст статьи извлечен, длина: {len(article_text)} символов")
            except Exception as e:
                logger.error(f"Ошибка извлечения текста из {article_url}: {e}")
                return jsonify({'success': False, 'error': f'Не удалось извлечь текст статьи: {str(e)}'}), 400
        
        if not article_text or len(article_text) < 50:
            logger.error("Текст пуст или слишком короткий")
            return jsonify({'success': False, 'error': f'Текст статьи слишком короткий ({len(article_text) if article_text else 0} символов). Минимум 50 символов.'}), 400
        
        # Рерайтим через выбранный провайдер
        logger.info(f"Рерайт статьи через {provider} в стиле: {style}, длина текста: {len(article_text)}")
        try:
            if provider == 'qwen':
                rewritten_text = rewrite_article_with_openrouter(article_text, style)
            elif provider == 'yandex':
                rewritten_text = rewrite_article_with_yandex(article_text, style)
            elif provider in ['rut5', 'flant5']:
                # Используем ML service для парафразирования
                rewritten_text = rewrite_article_with_ml(article_text, provider)
            
            logger.info(f"Статья обработана, длина результата: {len(rewritten_text)} символов")
            
            # Добавляем источник в конце текста (только если был передан URL)
            if article_url and article_url.strip():
                rewritten_text = rewritten_text.rstrip() + f"\n\nИсточник: {article_url}"
                logger.info("Источник добавлен в конец текста")
        except Exception as e:
            logger.error(f"Ошибка рерайта через {provider}: {e}")
            return jsonify({'success': False, 'error': f'Ошибка рерайта: {str(e)}'}), 500
        
        # Получаем три варианта изображений
        logger.info("Начинаем получение изображений...")
        
        # 1. Изображение из оригинальной статьи (только если был передан URL)
        original_image = None
        if article_url:
            logger.info("Извлечение изображения из оригинальной статьи...")
            original_image = extract_image_from_url(article_url)
            logger.info(f"Оригинальное изображение: {'найдено' if original_image else 'не найдено'}")
        else:
            logger.info("Пропускаем извлечение изображения из статьи (передан прямой текст)")
        
        # 2. Поиск через Pexels API или Unsplash
        # Извлекаем ключевые слова из статьи (пропускаем служебные слова в начале)
        search_query = extract_keywords_for_image_search(article_text, rewritten_text)
        logger.info(f"Поиск изображения через API для запроса: {search_query[:50]}...")
        
        pexels_image = search_image_from_pexels(search_query)
        if not pexels_image:
            # Если Pexels не сработал, пробуем Unsplash
            logger.info("Pexels не вернул изображение, пробуем Unsplash...")
            pexels_image = search_image_from_unsplash(search_query)
            if pexels_image:
                logger.info("Найдено изображение через Unsplash")
        
        logger.info(f"Изображение из API: {'найдено' if pexels_image else 'не найдено'}")
        
        # 3. Генерация через Kandinsky (используем начало статьи как промпт)
        # Убираем HTML теги из текста перед формированием промпта
        clean_text = re.sub(r'<[^>]+>', '', rewritten_text)  # Убираем все HTML теги
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()  # Убираем лишние пробелы
        generation_prompt = ' '.join(clean_text.split()[:30])  # Первые 30 слов переписанной статьи
        logger.info(f"Генерация изображения через Kandinsky с промптом: {generation_prompt[:50]}...")
        generated_image = generate_image_with_kandinsky(generation_prompt)
        logger.info(f"Сгенерированное изображение: {'получено' if generated_image else 'не получено'}")
        
        images = {
            'original': original_image,
            'pexels': pexels_image,
            'generated': generated_image
        }
        
        logger.info(f"Итоговые изображения: original={bool(original_image)}, pexels={bool(pexels_image)}, generated={bool(generated_image)}")
        
        # Сохраняем данные в БД (если доступна)
        url_id = None
        if DB_AVAILABLE:
            try:
                # Пытаемся получить username из разных источников
                username = data.get('username', None)
                
                # Если username не передан, пытаемся получить из токена авторизации
                if not username:
                    # Проверяем заголовок Authorization
                    auth_header = request.headers.get('Authorization', '')
                    token = None
                    if auth_header.startswith('Bearer '):
                        token = auth_header.replace('Bearer ', '')
                    elif auth_header:
                        token = auth_header
                    
                    # Или из query параметра
                    if not token:
                        token = request.args.get('token', None)
                    
                    if token:
                        user_data = verify_auth_token(token)
                        if user_data:
                            username = user_data.get('username') or (f"telegram_{user_data.get('id')}" if user_data.get('id') else None)
                
                # Если username все еще не найден, используем default_user
                if not username:
                    username = 'default_user'
                
                user = get_or_create_user(username=username)
                
                if user:
                    # Сохраняем URL только если он был передан (не прямой текст)
                    import time
                    start_time = time.time()
                    user_url = None
                    if article_url:
                        # Пытаемся извлечь заголовок из URL
                        title = None
                        try:
                            # Пытаемся получить заголовок из HTML
                            response = requests.get(article_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                            if response.status_code == 200:
                                soup = BeautifulSoup(response.text, 'html.parser')
                                title_tag = soup.find('title')
                                if title_tag:
                                    title = title_tag.get_text().strip()[:500]
                        except:
                            pass
                        
                        user_url = save_user_url(
                            user_id=user.id,
                            url=article_url,
                            title=title
                        )
                    else:
                        # Если передан прямой текст, создаем "фиктивный" URL для сохранения в БД
                        # Используем первые 100 символов текста как заголовок
                        title = article_text[:100] if len(article_text) > 100 else article_text
                        # Создаем "фиктивный" URL для идентификации текстового ввода
                        fake_url = f"text_input_{int(time.time())}"
                        user_url = save_user_url(
                            user_id=user.id,
                            url=fake_url,
                            title=title
                        )
                    
                    if user_url:
                        url_id = user_url.id
                        # Определяем язык текста
                        try:
                            from langdetect import detect
                            language = detect(article_text)
                        except:
                            language = 'ru'  # По умолчанию
                        
                        # Сохраняем результат обработки
                        processing_time = time.time() - start_time
                        save_processing_result(
                            url_id=url_id,
                            original_text=article_text[:50000],  # Ограничиваем размер
                            paraphrased_text=rewritten_text[:50000],
                            language=language,
                            processing_time=processing_time,
                            meta_data={
                                'style': style,
                                'provider': provider,
                                'images_count': len([img for img in images.values() if img]),
                                'is_direct_text': not bool(article_url)  # Помечаем, что это прямой текст
                            }
                        )
                        logger.info(f"✅ Данные сохранены в БД: user_id={user.id}, url_id={url_id}")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось сохранить данные в БД: {e}")
        
        return jsonify({
            'success': True,
            'original_text': article_text[:1000] + '...' if len(article_text) > 1000 else article_text,
            'text': rewritten_text,
            'rewritten_text': rewritten_text,  # Для совместимости
            'url': article_url if article_url else None,  # URL только если был передан
            'style': style,
            'provider': provider,
            'images': images,
            'url_id': url_id  # ID сохраненной записи (если БД доступна и был передан URL)
        }), 200
        
    except requests.exceptions.HTTPError as e:
        # Получаем URL из запроса безопасно
        try:
            request_data = request.json if request.is_json else {}
            request_url = request_data.get('url', 'неизвестный URL')
        except:
            request_url = 'неизвестный URL'
            
        if e.response and e.response.status_code == 403:
            error_msg = f"Сайт блокирует доступ (403 Forbidden). Возможно, требуется авторизация или сайт защищен от автоматических запросов."
            logger.error(f"Ошибка обработки статьи (403): {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg,
                'details': f'URL: {request_url}'
            }), 403
        else:
            error_msg = f"Ошибка при доступе к сайту: {str(e)}"
            logger.error(f"Ошибка обработки статьи (HTTP): {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
    except ValueError as e:
        logger.error(f"Ошибка валидации: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Неожиданная ошибка рерайта статьи: {e}", exc_info=True)
        import traceback
        logger.error(f"Полный traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/send-article', methods=['POST'])
def send_article():
    """Отправляет статью в каналы через Telegram Bot API"""
    if not AIOGRAM_AVAILABLE:
        return jsonify({
            'success': False, 
            'error': 'aiogram не установлен. Установите зависимости: pip install -r requirements.txt'
        }), 503
    
    try:
        data = request.json
        article_text = data.get('article_text', '')
        image_url = data.get('image_url')  # URL выбранного изображения
        selected_channels = data.get('channels', [])  # Список ID каналов для отправки
        
        logger.info(f"Получен запрос на отправку статьи. Длина текста: {len(article_text)}, image_url: {image_url[:100] if image_url else 'не указан'}...")
        
        if not article_text.strip():
            return jsonify({'success': False, 'error': 'Текст статьи не может быть пустым'}), 400
        
        # Загружаем каналы
        all_channels = load_channels()
        
        # Если указаны конкретные каналы, используем их, иначе все
        if selected_channels:
            channels_to_send = [ch for ch in all_channels if ch['id'] in selected_channels]
        else:
            channels_to_send = all_channels
        
        if not channels_to_send:
            return jsonify({'success': False, 'error': 'Каналы не настроены'}), 400
        
        success_count = 0
        failed_channels = []
        
        # Функция для очистки HTML тегов из текста для Telegram
        def clean_html_for_telegram(text):
            """Убирает HTML теги из текста, оставляя только текст"""
            import re
            # Убираем все HTML теги
            text = re.sub(r'<[^>]+>', '', text)
            # Заменяем множественные пробелы на одинарные
            text = re.sub(r'\s+', ' ', text)
            # Заменяем HTML entities
            text = text.replace('&nbsp;', ' ')
            text = text.replace('&amp;', '&')
            text = text.replace('&lt;', '<')
            text = text.replace('&gt;', '>')
            text = text.replace('&quot;', '"')
            text = text.replace('&#39;', "'")
            return text.strip()
        
        # Очищаем текст от HTML тегов перед отправкой
        clean_article_text = clean_html_for_telegram(article_text)
        
        # Асинхронная функция для отправки сообщений
        async def send_messages():
            nonlocal success_count, failed_channels
            # Создаём новый экземпляр Bot для этого запроса
            current_bot = Bot(token=BOT_TOKEN)
            try:
                for channel in channels_to_send:
                    try:
                        # Отправляем сообщение с изображением, если оно есть
                        if image_url and image_url.strip():
                            logger.info(f"📷 Отправка статьи С ИЗОБРАЖЕНИЕМ в канал {channel['name']} ({channel['id']})")
                            logger.info(f"   URL изображения: {image_url}")
                            try:
                                # Telegram может принимать URL напрямую, но лучше проверить
                                # Если URL не работает, можно скачать изображение и отправить как файл
                                
                                await current_bot.send_photo(
                                    chat_id=channel['id'],
                                    photo=image_url,
                                    caption=clean_article_text[:1024],  # Ограничиваем длину подписи (макс 1024 символа)
                                    parse_mode=None  # Не используем HTML парсинг для подписи
                                )
                                logger.info(f"✅ Статья с изображением успешно отправлена в канал: {channel['name']} ({channel['id']})")
                            except Exception as photo_error:
                                # Если не удалось отправить с фото, пробуем скачать и отправить как файл
                                logger.warning(f"Не удалось отправить фото по URL в {channel['name']}: {photo_error}")
                                try:
                                    # Пробуем скачать изображение и отправить как файл
                                    try:
                                        import aiohttp
                                    except ImportError:
                                        logger.error("aiohttp не установлен. Установите: pip install aiohttp")
                                        raise Exception("aiohttp не установлен")
                                    
                                    async with aiohttp.ClientSession() as session:
                                        async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                                            if resp.status == 200:
                                                image_data = await resp.read()
                                                from io import BytesIO
                                                
                                                # Используем BufferedInputFile для отправки BytesIO в aiogram 3.x
                                                try:
                                                    from aiogram.types import BufferedInputFile
                                                    input_photo = BufferedInputFile(image_data, filename='image.jpg')
                                                except ImportError:
                                                    # Если BufferedInputFile недоступен, используем InputFile
                                                    photo_file = BytesIO(image_data)
                                                    photo_file.name = 'image.jpg'
                                                    input_photo = InputFile(photo_file, filename='image.jpg')
                                                
                                                await current_bot.send_photo(
                                                    chat_id=channel['id'],
                                                    photo=input_photo,
                                                    caption=clean_article_text[:1024],
                                                    parse_mode=None  # Не используем HTML парсинг
                                                )
                                                logger.info(f"✅ Статья с изображением (скачанным) отправлена в канал: {channel['name']}")
                                            else:
                                                raise Exception(f"Не удалось скачать изображение: статус {resp.status}")
                                except Exception as download_error:
                                    # Если и скачивание не помогло, отправляем только текст
                                    logger.warning(f"Не удалось отправить фото (скачивание тоже не помогло) в {channel['name']}: {download_error}, отправляем только текст")
                                    await current_bot.send_message(
                                        chat_id=channel['id'],
                                        text=clean_article_text,
                                        parse_mode=None  # Не используем HTML парсинг
                                    )
                        else:
                            logger.info(f"📝 Отправка статьи БЕЗ ИЗОБРАЖЕНИЯ в канал {channel['name']} ({channel['id']})")
                            await current_bot.send_message(
                                chat_id=channel['id'],
                                text=clean_article_text,
                                parse_mode=None  # Не используем HTML парсинг
                            )
                        success_count += 1
                        logger.info(f"Статья отправлена в канал: {channel['name']} ({channel['id']})")
                    except TelegramAPIError as e:
                        error_msg = str(e)
                        failed_channels.append({
                            'channel': channel['name'],
                            'error': error_msg
                        })
                        logger.error(f"Ошибка отправки в канал {channel['name']}: {error_msg}")
                    except Exception as e:
                        failed_channels.append({
                            'channel': channel.get('name', channel['id']),
                            'error': str(e)
                        })
                        logger.error(f"Ошибка отправки в канал {channel['id']}: {e}")
            finally:
                # Закрываем сессию бота после отправки
                await current_bot.session.close()
        
        # Запускаем асинхронную функцию
        # Всегда создаём новый event loop для каждого запроса
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(send_messages())
        except Exception as e:
            logger.error(f"Ошибка работы с event loop: {e}")
            raise
        finally:
            # Закрываем loop после использования
            try:
                # Отменяем все незавершённые задачи
                pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
                for task in pending:
                    task.cancel()
                # Ждём отмены задач
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            finally:
                if not loop.is_closed():
                    loop.close()
        
        return jsonify({
            'success': True,
            'sent': success_count,
            'total': len(channels_to_send),
            'failed': failed_channels
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка обработки запроса: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/channels', methods=['GET'])
def get_channels():
    """Возвращает список доступных каналов"""
    try:
        channels = load_channels()
        return jsonify({
            'success': True,
            'channels': channels
        }), 200
    except Exception as e:
        logger.error(f"Ошибка получения каналов: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Проверка работоспособности сервера"""
    return jsonify({'status': 'ok'}), 200


@app.route('/api/auth/generate-token', methods=['POST', 'OPTIONS'])
def generate_token():
    """Генерирует новый токен для авторизации через бота"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        token = generate_auth_token()
        return jsonify({
            'success': True,
            'token': token,
            'expires_in': None  # Бессрочный токен (действителен пока пользователь авторизован)
        }), 200
    except Exception as e:
        logger.error(f"Ошибка генерации токена: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auth/verify-token', methods=['POST', 'OPTIONS'])
def verify_token():
    """Проверяет токен и возвращает данные пользователя"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.json
        token = data.get('token')
        
        if not token:
            return jsonify({'success': False, 'error': 'Токен не предоставлен'}), 400
        
        user_data = verify_auth_token(token)
        
        if user_data:
            return jsonify({
                'success': True,
                'authorized': True,
                'user': user_data
            }), 200
        else:
            return jsonify({
                'success': True,
                'authorized': False,
                'message': 'Токен не найден или не авторизован'
            }), 200
            
    except Exception as e:
        logger.error(f"Ошибка проверки токена: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auth/authorize', methods=['POST', 'OPTIONS'])
def authorize():
    """Авторизует токен с данными пользователя (вызывается ботом)"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.json
        token = data.get('token')
        user_data = data.get('user_data')
        
        if not token or not user_data:
            return jsonify({'success': False, 'error': 'Недостаточно данных'}), 400
        
        # Создаем/находим пользователя в БД при авторизации
        if DB_AVAILABLE:
            try:
                from database import get_or_create_user
                # Получаем username из данных Telegram
                username = user_data.get('username')
                if not username and user_data.get('id'):
                    username = f"telegram_{user_data.get('id')}"
                
                if username:
                    user = get_or_create_user(username=username, email=None)
                    if user:
                        logger.info(f"✅ Пользователь создан/найден в БД: {username} (ID: {user.id})")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось создать пользователя в БД при авторизации: {e}")
        
        if authorize_token(token, user_data):
            logger.info(f"Токен {token[:10]}... успешно авторизован для пользователя {user_data.get('id')}")
            return jsonify({'success': True}), 200
        else:
            return jsonify({'success': False, 'error': 'Токен не найден или истек'}), 404
            
    except Exception as e:
        logger.error(f"Ошибка авторизации токена: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# API Endpoints для работы с БД
# ============================================

@app.route('/api/users/<username>/urls', methods=['GET'])
def get_user_urls_endpoint(username):
    """Получить все URL пользователя"""
    if not DB_AVAILABLE:
        return jsonify({'success': False, 'error': 'База данных недоступна'}), 503
    
    try:
        from database import get_or_create_user, get_user_urls
        
        user = get_or_create_user(username=username)
        if not user:
            return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
        
        urls = get_user_urls(user.id)
        
        return jsonify({
            'success': True,
            'user_id': user.id,
            'username': user.username,
            'urls': [
                {
                    'id': url.id,
                    'url': url.url,
                    'title': url.title,
                    'status': url.status,
                    'created_at': url.created_at.isoformat() if url.created_at else None,
                    'last_processed_at': url.last_processed_at.isoformat() if url.last_processed_at else None
                }
                for url in urls
            ],
            'total': len(urls)
        }), 200
    except Exception as e:
        logger.error(f"Ошибка получения URL пользователя: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/users/<username>/stats', methods=['GET'])
def get_user_stats_endpoint(username):
    """Получить статистику пользователя"""
    if not DB_AVAILABLE:
        return jsonify({'success': False, 'error': 'База данных недоступна'}), 503
    
    try:
        from database import get_or_create_user, get_user_stats
        
        user = get_or_create_user(username=username)
        if not user:
            return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
        
        stats = get_user_stats(user.id)
        
        return jsonify({
            'success': True,
            'user_id': user.id,
            'username': user.username,
            'stats': stats
        }), 200
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/urls/<int:url_id>/results', methods=['GET'])
def get_url_processing_results_endpoint(url_id):
    """Получить результаты обработки URL"""
    if not DB_AVAILABLE:
        return jsonify({'success': False, 'error': 'База данных недоступна'}), 503
    
    try:
        from database import get_url_by_id, get_processing_results
        
        url = get_url_by_id(url_id)
        if not url:
            return jsonify({'success': False, 'error': 'URL не найден'}), 404
        
        results = get_processing_results(url_id, limit=10)
        
        return jsonify({
            'success': True,
            'url_id': url_id,
            'url': url.url,
            'results': [
                {
                    'id': result.id,
                    'original_text': result.original_text[:500] + '...' if result.original_text and len(result.original_text) > 500 else result.original_text,
                    'paraphrased_text': result.paraphrased_text[:500] + '...' if result.paraphrased_text and len(result.paraphrased_text) > 500 else result.paraphrased_text,
                    'summarized_text': result.summarized_text[:500] + '...' if result.summarized_text and len(result.summarized_text) > 500 else result.summarized_text,
                    'language': result.language,
                    'processing_time': result.processing_time,
                    'created_at': result.created_at.isoformat() if result.created_at else None,
                    'metadata': result.meta_data
                }
                for result in results
            ],
            'total': len(results)
        }), 200
    except Exception as e:
        logger.error(f"Ошибка получения результатов обработки: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/users', methods=['GET'])
def list_users_endpoint():
    """Получить список всех пользователей (для админов)"""
    if not DB_AVAILABLE:
        return jsonify({'success': False, 'error': 'База данных недоступна'}), 503
    
    try:
        from database import get_db_session
        from models import User
        
        session = get_db_session()
        if not session:
            return jsonify({'success': False, 'error': 'Не удалось подключиться к БД'}), 503
        
        users = session.query(User).all()
        session.close()
        
        return jsonify({
            'success': True,
            'users': [
                {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                }
                for user in users
            ],
            'total': len(users)
        }), 200
    except Exception as e:
        logger.error(f"Ошибка получения списка пользователей: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/save-url', methods=['POST', 'OPTIONS'])
def save_url():
    """Сохраняет URL пользователя в БД без обработки статьи"""
    if request.method == 'OPTIONS':
        return '', 200
    
    if not DB_AVAILABLE:
        return jsonify({'success': False, 'error': 'База данных недоступна'}), 503
    
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Требуется JSON'}), 400
        
        data = request.json
        article_url = data.get('url')
        
        if not article_url:
            return jsonify({'success': False, 'error': 'URL не предоставлен'}), 400
        
        from database import get_or_create_user, save_user_url
        
        # Пытаемся получить username из разных источников
        username = data.get('username', None)
        
        # Если username не передан, пытаемся получить из токена авторизации
        if not username:
            auth_header = request.headers.get('Authorization', '')
            token = None
            if auth_header.startswith('Bearer '):
                token = auth_header.replace('Bearer ', '').strip()
            elif auth_header:
                token = auth_header.strip()
            
            if not token:
                token = request.args.get('token', None)
            
            if token:
                logger.info(f"🔍 Проверка токена для сохранения URL: {token[:10] if len(token) > 10 else token}...")
                user_data = verify_auth_token(token)
                if user_data:
                    username = user_data.get('username')
                    if not username and user_data.get('id'):
                        username = f"telegram_{user_data.get('id')}"
                    logger.info(f"✅ Username извлечен из токена: {username} (ID: {user_data.get('id')})")
                else:
                    logger.warning(f"⚠️ Токен не прошел проверку или истек. Проверяю auth_tokens...")
                    # Дополнительная проверка - возможно токен в другом формате
                    load_auth_tokens()
                    logger.warning(f"⚠️ Всего токенов в системе: {len(auth_tokens)}")
            else:
                logger.warning("⚠️ Токен авторизации не найден в заголовках")
                logger.warning(f"⚠️ Authorization header: {auth_header[:50] if auth_header else 'None'}...")
        
        # Если username все еще не найден, пытаемся получить из сохраненного пользователя
        if not username:
            # Пытаемся получить из токена еще раз, но уже без Bearer префикса
            auth_header = request.headers.get('Authorization', '')
            if auth_header:
                token = auth_header.replace('Bearer ', '').strip()
                if token:
                    user_data = verify_auth_token(token)
                    if user_data:
                        username = user_data.get('username') or (f"telegram_{user_data.get('id')}" if user_data.get('id') else None)
        
        # Если username все еще не найден, используем default_user (но логируем это)
        if not username:
            logger.warning("⚠️ Username не найден, используется default_user")
            username = 'default_user'
        
        user = get_or_create_user(username=username)
        
        if not user:
            return jsonify({'success': False, 'error': 'Не удалось создать/найти пользователя'}), 500
        
        # Пытаемся извлечь заголовок из URL
        title = None
        try:
            response = requests.get(article_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text().strip()[:500]
        except:
            pass
        
        user_url = save_user_url(
            user_id=user.id,
            url=article_url,
            title=title
        )
        
        if user_url:
            logger.info(f"✅ URL сохранен в БД: {article_url} для пользователя {username} (ID: {user.id})")
            return jsonify({
                'success': True,
                'url_id': user_url.id,
                'url': user_url.url,
                'title': user_url.title,
                'username': username,
                'user_id': user.id,
                'message': 'URL успешно сохранен'
            }), 200
        else:
            logger.error(f"❌ Не удалось сохранить URL для пользователя {username}")
            return jsonify({'success': False, 'error': 'Не удалось сохранить URL'}), 500
            
    except Exception as e:
        logger.error(f"Ошибка сохранения URL: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/data', methods=['GET'])
def get_all_data():
    """Получить все данные в табличном формате: все пользователи и их URL
    
    Возвращает данные всех пользователей системы.
    Параметры запроса:
    - username (опционально): если указан, возвращает данные только этого пользователя
    """
    if not DB_AVAILABLE:
        return jsonify({'success': False, 'error': 'База данных недоступна'}), 503
    
    try:
        from database import get_db_session, get_or_create_user
        from models import User, UserUrl, UrlProcessingResult
        
        # Получаем username из query параметров (опционально)
        username = request.args.get('username', None)
        
        session = get_db_session()
        if not session:
            return jsonify({'success': False, 'error': 'Не удалось подключиться к БД'}), 503
        
        # Если указан username, получаем данные только этого пользователя
        if username:
            # Получаем пользователя в текущей сессии (без eager loading, загрузим URLs отдельно)
            user = session.query(User).filter(User.username == username).first()
            if not user:
                # Если пользователь не найден, создаем его прямо в текущей сессии
                user = User(
                    username=username,
                    email=None,
                    password_hash="demo_hash",
                    is_active=True
                )
                session.add(user)
                session.commit()
                session.refresh(user)
            users = [user]
        else:
            # Получаем всех пользователей (URLs загрузим отдельно)
            users = session.query(User).all()
        
        # Формируем таблицу данных
        table_data = []
        for user in users:
            # Загружаем URLs для пользователя явно через запрос
            user_urls = session.query(UserUrl).filter(UserUrl.user_id == user.id).all()
            # Если у пользователя нет URL, все равно добавляем его в результат
            if not user_urls:
                table_data.append({
                    'user_id': user.id,
                    'username': user.username,
                    'user_email': user.email,
                    'url_id': None,
                    'url': None,
                    'url_title': None,
                    'url_status': None,
                    'url_created_at': None,
                    'url_last_processed_at': None,
                    'has_processing_result': False,
                    'processing_language': None,
                    'processing_time': None,
                    'last_result_created_at': None
                })
            else:
                for url in user_urls:
                    # Получаем последний результат обработки
                    last_result = session.query(UrlProcessingResult).filter(
                        UrlProcessingResult.url_id == url.id
                    ).order_by(UrlProcessingResult.created_at.desc()).first()
                    
                    table_data.append({
                        'user_id': user.id,
                        'username': user.username,
                        'user_email': user.email,
                        'url_id': url.id,
                        'url': url.url,
                        'url_title': url.title,
                        'url_status': url.status,
                        'url_created_at': url.created_at.isoformat() if url.created_at else None,
                        'url_last_processed_at': url.last_processed_at.isoformat() if url.last_processed_at else None,
                        'has_processing_result': last_result is not None,
                        'processing_language': last_result.language if last_result else None,
                        'processing_time': last_result.processing_time if last_result else None,
                        'last_result_created_at': last_result.created_at.isoformat() if last_result and last_result.created_at else None
                    })
        
        session.close()
        
        return jsonify({
            'success': True,
            'data': table_data,
            'total': len(table_data),
            'users_count': len(users),
            'filtered_by_username': username if username else None
        }), 200
    except Exception as e:
        logger.error(f"Ошибка получения данных: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
