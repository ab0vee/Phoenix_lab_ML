"""Главный файл FastAPI приложения"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from api.routes import paraphrase, summarize, summarize_url, process, similarity, health
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    print(f"ML Service запущен на {settings.api_host}:{settings.api_port}")
    print(f"Модель: {settings.ml_model_name}")
    print(f"Кэш: {'включен' if settings.cache_enabled else 'выключен'}")
    print(f"Автозагрузка моделей: {'включена' if settings.auto_download_models else 'выключена'}")
    
    # Предзагрузка моделей при старте (если включена)
    if settings.preload_models:
        print("\n🔄 Предзагрузка моделей...")
        print("Это может занять 10-20 минут при первом запуске...\n")
        import gc
        import time
        import torch
        from services.text_processor import TextProcessor
        processor = TextProcessor()
        
        def cleanup_memory():
            """Очистка памяти после загрузки модели"""
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            time.sleep(2)  # Небольшая пауза для освобождения памяти
        
        # Парафразирование (русская модель)
        print("📥 Загрузка модели парафразирования (русский)...")
        try:
            processor._load_paraphrase_model('ru')
            print("✅ Модель парафразирования (ru) загружена")
            cleanup_memory()
        except Exception as e:
            print(f"❌ Ошибка загрузки модели парафразирования (ru): {e}")
            cleanup_memory()
        
        # Парафразирование (английская модель)
        print("📥 Загрузка модели парафразирования (английский)...")
        try:
            processor._load_paraphrase_model('en')
            print("✅ Модель парафразирования (en) загружена")
            cleanup_memory()
        except Exception as e:
            print(f"⚠️  Модель парафразирования (en) не загружена: {e}")
            cleanup_memory()
        
        # Суммаризация (русская модель)
        print("📥 Загрузка модели суммаризации (русский)...")
        try:
            processor._load_summary_model_ru()
            print("✅ Модель суммаризации (ru) загружена")
            cleanup_memory()
        except Exception as e:
            print(f"❌ Ошибка загрузки модели суммаризации (ru): {e}")
            cleanup_memory()
        
        print("\n✨ Предзагрузка завершена! Все модели готовы к работе.\n")
    else:
        print("⚡ Режим Lazy Loading: модели будут загружены при первом запросе\n")
    
    print("Сервер готов к работе!")
    yield
    # Shutdown
    print("ML Service остановлен")


# Создание приложения
app = FastAPI(
    title="Phoenix LAB ML Service",
    description="""
    # 🤖 ML Service для обработки новостного контента
    
    ## Возможности:
    - 🔄 **Парафразирование** текста (изменение формулировок без потери смысла)
    - 📝 **Суммаризация** длинных текстов
    - 📊 **Проверка схожести** текстов
    - 🌐 **Полная обработка** новостей с адаптацией для разных платформ
    
    ## Модели:
    - **Парафразирование:** google/flan-t5-large
    - **Суммаризация:** IlyaGusev/mbart_ru_sum_gazeta (RU), facebook/bart-large-cnn (EN)
    - **Схожесть:** sentence-transformers/paraphrase-multilingual-mpnet-base-v2
    
    ## Как тестировать:
    1. Выберите нужный endpoint ниже
    2. Нажмите "Try it out"
    3. Отредактируйте JSON (или используйте пример)
    4. Нажмите "Execute"
    5. Посмотрите результат
    
    **Примечание:** Первый запрос может занять 1-2 минуты (загрузка модели в память).
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Корневой роут
@app.get("/")
async def root():
    """Корневой endpoint с информацией об API"""
    return {
        "service": "Phoenix LAB ML Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "test_page": "/test",
        "health": "/health",
        "endpoints": {
            "health": "/health",
            "paraphrase": "/api/v1/paraphrase (POST)",
            "summarize": "/api/v1/summarize (POST)",
            "process": "/api/v1/process (POST)",
            "similarity": "/api/v1/similarity (POST)"
        },
        "note": "POST endpoints требуют тело запроса. Используйте /docs или /test для тестирования"
    }

# Тестовая страница для API
@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """Страница для тестирования API"""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Phoenix LAB ML Service API</title>
    <style>
        body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; background: #1e1e1e; color: #fff; }
        .endpoint { background: #2d2d2d; padding: 20px; margin: 20px 0; border-radius: 8px; }
        button { background: #007acc; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin: 10px 5px; }
        button:hover { background: #005a9e; }
        input, textarea { width: 100%; padding: 8px; margin: 5px 0; background: #3d3d3d; color: #fff; border: 1px solid #555; border-radius: 4px; }
        .result { background: #252525; padding: 15px; margin-top: 10px; border-radius: 4px; white-space: pre-wrap; font-family: monospace; }
        h2 { color: #4ec9b0; }
        .link { color: #4ec9b0; text-decoration: none; }
    </style>
</head>
<body>
    <h1>🧪 Тестирование Phoenix LAB ML Service API</h1>
    <p><strong>Важно:</strong> POST endpoints нельзя открыть напрямую в браузере. Используйте эту страницу или <a href="/docs" class="link">Swagger UI</a>.</p>
    
    <div class="endpoint">
        <h2>1. Health Check</h2>
        <button onclick="testHealth()">Проверить /health</button>
        <div id="healthResult" class="result" style="display:none;"></div>
    </div>

    <div class="endpoint">
        <h2>2. Summarize (Суммаризация)</h2>
        <textarea id="summarizeText" rows="8">Американская компания Nike заявила о возможных дополнительных издержках в размере $1 млрд в результате действия импортных пошлин, введённых администрацией Дональда Трампа. По словам финансового директора Мэттью Френда, новые пошлины стали существенным фактором давления на издержки. Nike планирует компенсировать их за счёт оптимизации цепочек поставок и частичного перекладывания затрат на потребителей. Чистая прибыль компании по итогам IV квартала сократилась на 86% до $211 млн против $1,5 млрд годом ранее.</textarea>
        <button onclick="testSummarize()">Суммаризировать</button>
        <div id="summarizeResult" class="result" style="display:none;"></div>
    </div>

    <div class="endpoint">
        <h2>3. Summarize from URL (Суммаризация из URL)</h2>
        <input type="url" id="urlInput" placeholder="https://lenta.ru/news/..." style="width: 100%; margin-bottom: 10px;">
        <button onclick="testSummarizeUrl()">Извлечь и суммаризировать</button>
        <div id="urlResult" class="result" style="display:none;"></div>
    </div>

    <div class="endpoint">
        <h2>4. Paraphrase (Парафразирование)</h2>
        <textarea id="paraphraseText" rows="3">Сегодня хорошая погода</textarea>
        <button onclick="testParaphrase()">Парафразировать</button>
        <div id="paraphraseResult" class="result" style="display:none;"></div>
    </div>

    <script>
        async function testHealth() {
            const response = await fetch('/health');
            const data = await response.json();
            document.getElementById('healthResult').style.display = 'block';
            document.getElementById('healthResult').textContent = JSON.stringify(data, null, 2);
        }
        async function testSummarize() {
            const text = document.getElementById('summarizeText').value;
            const btn = event.target;
            const resultDiv = document.getElementById('summarizeResult');
            btn.disabled = true;
            btn.textContent = 'Обработка...';
            resultDiv.style.display = 'block';
            resultDiv.textContent = 'Обработка...';
            try {
                const response = await fetch('/api/v1/summarize', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: text})
                });
                
                if (!response.ok) {
                    const errorText = await response.text();
                    let errorData;
                    try {
                        errorData = JSON.parse(errorText);
                        resultDiv.textContent = 'Ошибка: ' + (errorData.detail || errorData.message || `HTTP ${response.status}`);
                    } catch {
                        resultDiv.textContent = 'Ошибка: ' + (errorText || `HTTP ${response.status} ${response.statusText}`);
                    }
                    return;
                }
                
                const data = await response.json();
                resultDiv.textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                resultDiv.textContent = 'Ошибка подключения: ' + error.message;
            } finally {
                btn.disabled = false;
                btn.textContent = 'Суммаризировать';
            }
        }
        async function testSummarizeUrl() {
            const url = document.getElementById('urlInput').value;
            if (!url) {
                alert('Введите URL');
                return;
            }
            const btn = event.target;
            const resultDiv = document.getElementById('urlResult');
            btn.disabled = true;
            btn.textContent = 'Извлечение и обработка... (может занять 30-60 сек)';
            resultDiv.style.display = 'block';
            resultDiv.textContent = 'Обработка...';
            try {
                const response = await fetch('/api/v1/summarize-url', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url: url})
                });
                
                if (!response.ok) {
                    const errorText = await response.text();
                    let errorData;
                    try {
                        errorData = JSON.parse(errorText);
                        resultDiv.textContent = 'Ошибка: ' + (errorData.detail || errorData.message || `HTTP ${response.status}`);
                    } catch {
                        resultDiv.textContent = 'Ошибка: ' + errorText || `HTTP ${response.status} ${response.statusText}`;
                    }
                    return;
                }
                
                const data = await response.json();
                resultDiv.textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                resultDiv.textContent = 'Ошибка подключения: ' + error.message + '\n\nПроверьте:\n- Сервер запущен\n- URL корректный\n- Нет проблем с сетью';
            } finally {
                btn.disabled = false;
                btn.textContent = 'Извлечь и суммаризировать';
            }
        }
        async function testParaphrase() {
            const text = document.getElementById('paraphraseText').value;
            const resultDiv = document.getElementById('paraphraseResult');
            resultDiv.style.display = 'block';
            resultDiv.textContent = 'Обработка...';
            try {
                const response = await fetch('/api/v1/paraphrase', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: text, temperature: 0.7})
                });
                
                if (!response.ok) {
                    const errorText = await response.text();
                    let errorData;
                    try {
                        errorData = JSON.parse(errorText);
                        resultDiv.textContent = 'Ошибка: ' + (errorData.detail || errorData.message || `HTTP ${response.status}`);
                    } catch {
                        resultDiv.textContent = 'Ошибка: ' + (errorText || `HTTP ${response.status} ${response.statusText}`);
                    }
                    return;
                }
                
                const data = await response.json();
                resultDiv.textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                resultDiv.textContent = 'Ошибка подключения: ' + error.message;
            }
        }
    </script>
</body>
</html>
    """
    return html_content

# Подключение роутов
app.include_router(health.router, tags=["Health"])
app.include_router(paraphrase.router, prefix="/api/v1", tags=["Paraphrase"])
app.include_router(summarize.router, prefix="/api/v1", tags=["Summarize"])
app.include_router(summarize_url.router, prefix="/api/v1", tags=["Summarize URL"])
app.include_router(process.router, prefix="/api/v1", tags=["Process"])
app.include_router(similarity.router, prefix="/api/v1", tags=["Similarity"])


if __name__ == "__main__":
    import uvicorn
    import os
    # Отключаем hot-reload в Docker (экономит память)
    # В Docker файлы не меняются, поэтому reload не нужен
    enable_reload = os.getenv("ENABLE_RELOAD", "false").lower() == "true"
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=enable_reload,  # Отключено по умолчанию для экономии памяти
        timeout_keep_alive=120,  # Увеличенный таймаут для длительных запросов (2 минуты)
        timeout_graceful_shutdown=30
    )

