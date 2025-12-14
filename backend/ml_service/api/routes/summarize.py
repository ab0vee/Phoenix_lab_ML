"""Endpoint для суммаризации"""
from fastapi import APIRouter, HTTPException, Depends
from api.schemas import SummarizeRequest, SummarizeResponse
from api.dependencies import verify_api_key
from services.text_processor import TextProcessor
import time
import logging

router = APIRouter()
text_processor = TextProcessor()
logger = logging.getLogger(__name__)


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_text(
    request: SummarizeRequest,
    api_key: str = Depends(verify_api_key)
):
    """Суммаризация текста"""
    try:
        start_time = time.time()
        original_length = len(request.text)
        
        logger.info(f"Начало суммаризации текста длиной {original_length} символов")
        
        # Реальная суммаризация через модель
        summary = await text_processor.summarize(
            text=request.text,
            target_length=request.target_length,
            language=request.language
        )
        
        summary_length = len(summary)
        compression_ratio = summary_length / original_length if original_length > 0 else 0
        processing_time = time.time() - start_time
        
        logger.info(f"Суммаризация завершена: {original_length} -> {summary_length} символов за {processing_time:.2f}с")
        
        return SummarizeResponse(
            summary=summary,
            original_length=original_length,
            summary_length=summary_length,
            compression_ratio=round(compression_ratio, 3),
            processing_time=round(processing_time, 2),
            cached=False
        )
    except Exception as e:
        logger.error(f"Ошибка при суммаризации: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при суммаризации: {str(e)}"
        )

