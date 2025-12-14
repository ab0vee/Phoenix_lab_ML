"""Health check endpoint"""
from fastapi import APIRouter
from api.schemas import HealthResponse
from config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка состояния сервиса"""
    from services.text_processor import TextProcessor
    
    # Проверяем состояние моделей
    processor = TextProcessor()
    models_status = {
        "paraphrase_ru": processor.paraphrase_model_ru is not None,
        "paraphrase_en": processor.paraphrase_model_en is not None,
        "summary_ru": processor.summary_model_ru is not None,
    }
    
    # Сервис здоров если хотя бы основные модели загружены
    is_ready = models_status["paraphrase_ru"] or models_status["summary_ru"]
    
    return HealthResponse(
        status="ready" if is_ready else "loading",
        model_loaded=is_ready,
        cache_enabled=settings.cache_enabled,
        model_name=settings.ml_model_name,
        version="1.0.0",
        models_status=models_status  # Детальная информация о моделях
    )

