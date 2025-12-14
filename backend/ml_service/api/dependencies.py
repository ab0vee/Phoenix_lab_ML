"""Зависимости для API"""
from fastapi import Header, HTTPException, status
from typing import Optional
from config import settings


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    """Проверка API ключа"""
    # Временно отключено для тестирования
    # Раскомментируйте для продакшена:
    # if settings.api_key and x_api_key != settings.api_key:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Invalid API key"
    #     )
    pass

