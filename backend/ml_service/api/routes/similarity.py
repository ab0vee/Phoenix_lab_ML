"""Endpoint для проверки схожести"""
from fastapi import APIRouter, HTTPException, Depends
from api.schemas import SimilarityRequest, SimilarityResponse
from api.dependencies import verify_api_key
from services.text_processor import TextProcessor

router = APIRouter()
text_processor = TextProcessor()


@router.post("/similarity", response_model=SimilarityResponse)
async def check_similarity(
    request: SimilarityRequest,
    api_key: str = Depends(verify_api_key)
):
    """Проверка семантической схожести двух текстов"""
    try:
        similarity_score = await text_processor.check_similarity(
            request.text1,
            request.text2
        )
        
        return SimilarityResponse(
            similarity=similarity_score,
            is_similar=similarity_score >= request.threshold,
            threshold=request.threshold
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при проверке схожести: {str(e)}"
        )

