"""Endpoint для суммаризации контента по URL"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter()


class SummarizeUrlRequest(BaseModel):
    """Запрос на суммаризацию по URL"""
    url: HttpUrl = Field(..., description="URL новостной статьи", examples=["https://example.com/news/article"])
    target_length: Optional[int] = Field(None, description="Желаемая длина итога (в символах)", examples=[600])
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://lenta.ru/news/2024/01/15/tech/",
                "target_length": 600
            }
        }


class SummarizeUrlResponse(BaseModel):
    """Ответ с суммаризированным контентом"""
    url: str = Field(..., description="Исходный URL")
    title: Optional[str] = Field(None, description="Заголовок статьи")
    summary: str = Field(..., description="Краткое содержание")
    original_text: str = Field(..., description="Извлечённый полный текст")
    original_length: int = Field(..., description="Длина оригинального текста")
    summary_length: int = Field(..., description="Длина суммаризации")
    language: str = Field(..., description="Определённый язык текста", examples=["ru", "en"])
    processing_time: float = Field(..., description="Время обработки в секундах")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://lenta.ru/news/2024/01/15/tech/",
                "title": "Новые технологии в 2024 году",
                "summary": "Краткое содержание статьи...",
                "original_text": "Полный текст статьи...",
                "original_length": 5000,
                "summary_length": 600,
                "language": "ru",
                "processing_time": 15.5
            }
        }


@router.post(
    "/summarize-url",
    response_model=SummarizeUrlResponse,
    summary="Суммаризация статьи по URL",
    description="""
Извлекает текст статьи по URL и создаёт краткое содержание.

**Процесс:**
1. Загрузка HTML-страницы
2. Извлечение основного контента (заголовок + текст)
3. Очистка от рекламы и лишних элементов
4. Определение языка
5. Суммаризация с использованием подходящей модели
   - Русский: mbart_ru_sum_gazeta
   - Английский: bart-large-cnn

**Поддерживаемые сайты:**
- Большинство новостных порталов
- Оптимально работает с русскоязычными новостями
- Лучшие результаты на сайтах с чистой структурой статей

**Лимиты:**
- Максимальная длина статьи: ~5000 слов
- Рекомендуемое время обработки: 10-30 секунд
"""
)
async def summarize_from_url(request: SummarizeUrlRequest):
    """
    Извлечь и суммаризировать статью по URL
    """
    start_time = time.time()
    
    try:
        # Импортируем сервисы
        from services.content_extractor import ContentExtractor
        from services.text_processor import TextProcessor
        
        # Извлекаем контент из URL
        extractor = ContentExtractor()
        logger.info(f"Извлечение контента из URL: {request.url}")
        
        extracted = await extractor.extract_from_url(str(request.url))
        
        if not extracted or not extracted.get("text"):
            raise HTTPException(
                status_code=400,
                detail="Не удалось извлечь текст из URL. Проверьте корректность ссылки."
            )
        
        original_text = extracted["text"]
        title = extracted.get("title", "")
        original_length = len(original_text)
        
        logger.info(f"Извлечено {original_length} символов. Заголовок: {title}")
        
        # Суммаризация
        processor = TextProcessor()
        
        # Определяем язык
        language = processor._detect_language(original_text)
        logger.info(f"Определён язык: {language}")
        
        # Суммаризируем
        summary = await processor.summarize(
            text=original_text,
            target_length=request.target_length,
            language=language
        )
        
        summary_length = len(summary)
        processing_time = time.time() - start_time
        
        logger.info(f"Суммаризация завершена. Сокращение: {original_length} -> {summary_length} символов за {processing_time:.2f}с")
        
        return SummarizeUrlResponse(
            url=str(request.url),
            title=title,
            summary=summary,
            original_text=original_text,
            original_length=original_length,
            summary_length=summary_length,
            language=language,
            processing_time=round(processing_time, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обработке URL {request.url}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка обработки URL: {str(e)}"
        )




