"""Endpoint для полной обработки (fetch + summarize + paraphrase)"""
from fastapi import APIRouter, HTTPException, Depends
from api.schemas import ProcessRequest, ProcessResponse
from api.dependencies import verify_api_key
from services.content_extractor import ContentExtractor
from services.text_processor import TextProcessor
import time

router = APIRouter()
content_extractor = ContentExtractor()
text_processor = TextProcessor()


@router.post("/process", response_model=ProcessResponse)
async def process_news(
    request: ProcessRequest,
    api_key: str = Depends(verify_api_key)
):
    """Полная обработка новости: извлечение → суммаризация → парафразирование"""
    try:
        start_time = time.time()
        
        # Шаг 1: Извлечение контента
        if request.url:
            content_data = await content_extractor.extract_from_url(str(request.url))
            original_text = content_data.get("text", "")
            source_info = {
                "url": str(request.url),
                "title": content_data.get("title", ""),
                "language": content_data.get("language", "ru"),
                "original_length": len(original_text)
            }
        else:
            original_text = request.text
            source_info = {
                "text": original_text[:100] + "..." if len(original_text) > 100 else original_text,
                "language": "ru",  # TODO: определить язык
                "original_length": len(original_text)
            }
        
        if not original_text:
            raise HTTPException(status_code=400, detail="Не удалось извлечь текст")
        
        # Шаг 2: Суммаризация (если нужно)
        summary_data = None
        text_to_paraphrase = original_text
        
        # Проверка необходимости суммаризации
        should_summarize = (
            request.force_summarize or
            len(original_text) > 6000  # Порог для автоматической суммаризации
        )
        
        if should_summarize:
            summary = await text_processor.summarize(
                text=original_text,
                target_length=request.target_lengths.get("default", 600) if request.target_lengths else 600,
                language=source_info.get("language", "ru")
            )
            text_to_paraphrase = summary
            summary_data = {
                "text": summary,
                "original_length": len(original_text),
                "summary_length": len(summary)
            }
        
        # Шаг 3: Парафразирование
        paraphrased = await text_processor.paraphrase(text_to_paraphrase)
        
        # Проверка схожести
        similarity_score = await text_processor.check_similarity(
            original_text if not summary_data else summary_data["text"],
            paraphrased
        )
        
        # Шаг 4: Подготовка вариантов для платформ
        platform_variants = {}
        platform_limits = {
            "telegram": 4096,
            "vk": 10000,
            "instagram": 2200
        }
        
        for platform in request.platforms:
            limit = platform_limits.get(platform, 4096)
            variant = paraphrased[:limit] if len(paraphrased) > limit else paraphrased
            platform_variants[platform] = {
                "text": variant,
                "length": len(variant),
                "truncated": len(paraphrased) > limit
            }
        
        processing_time = time.time() - start_time
        
        return ProcessResponse(
            source=source_info,
            summary=summary_data,
            paraphrased={
                "text": paraphrased,
                "length": len(paraphrased)
            },
            platform_variants=platform_variants,
            similarity_score=similarity_score,
            processing_time=round(processing_time, 2),
            cached=False
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке: {str(e)}"
        )

