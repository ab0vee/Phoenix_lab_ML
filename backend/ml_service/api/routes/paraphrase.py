"""Endpoint для парафразирования"""
from fastapi import APIRouter, HTTPException, Depends
from api.schemas import ParaphraseRequest, ParaphraseResponse
from api.dependencies import verify_api_key
from services.text_processor import TextProcessor
import time

router = APIRouter()
text_processor = TextProcessor()


@router.post("/paraphrase", response_model=ParaphraseResponse)
async def paraphrase_text(
    request: ParaphraseRequest,
    api_key: str = Depends(verify_api_key)
):
    """Парафразирование текста"""
    try:
        start_time = time.time()
        
        # TODO: Реальная обработка через модель
        # Пока заглушка
        paraphrased = await text_processor.paraphrase(
            text=request.text,
            max_length=request.max_length,
            temperature=request.temperature,
            top_p=request.top_p,
            num_beams=request.num_beams
        )
        
        # Проверка схожести
        similarity_score = await text_processor.check_similarity(
            request.text,
            paraphrased
        )
        
        processing_time = time.time() - start_time
        
        return ParaphraseResponse(
            paraphrased=paraphrased,
            original=request.text,
            similarity_score=similarity_score,
            processing_time=round(processing_time, 2),
            cached=False
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при парафразировании: {str(e)}"
        )

