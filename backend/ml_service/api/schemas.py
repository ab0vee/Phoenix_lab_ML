"""Pydantic схемы для API"""
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, List, Dict
from datetime import datetime


class ParaphraseRequest(BaseModel):
    """Запрос на парафразирование"""
    text: str = Field(
        ..., 
        min_length=1, 
        max_length=10000, 
        description="Текст для парафразирования",
        examples=["Сегодня произошло важное событие в мире технологий."]
    )
    max_length: Optional[int] = Field(512, ge=50, le=1024, description="Максимальная длина результата")
    temperature: Optional[float] = Field(0.7, ge=0.1, le=1.0, description="Температура генерации")
    top_p: Optional[float] = Field(0.9, ge=0.1, le=1.0, description="Nucleus sampling")
    num_beams: Optional[int] = Field(5, ge=1, le=10, description="Количество beams")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Сегодня в Москве прошла важная встреча между представителями технологических компаний.",
                "max_length": 512,
                "temperature": 0.7,
                "top_p": 0.9,
                "num_beams": 5
            }
        }


class ParaphraseResponse(BaseModel):
    """Ответ на парафразирование"""
    paraphrased: str = Field(..., description="Парафразированный текст")
    original: str = Field(..., description="Исходный текст")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Семантическая схожесть")
    processing_time: float = Field(..., description="Время обработки в секундах")
    cached: bool = Field(False, description="Было ли взято из кэша")


class SummarizeRequest(BaseModel):
    """Запрос на суммаризацию"""
    text: str = Field(
        ..., 
        min_length=1, 
        max_length=50000, 
        description="Текст для суммаризации"
    )
    target_length: Optional[int] = Field(None, ge=50, le=2000, description="Целевая длина саммари")
    language: Optional[str] = Field(None, description="Язык текста (ru/en)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Сегодня в столице состоялась встреча представителей крупнейших технологических компаний страны. На повестке дня были вопросы развития искусственного интеллекта и внедрения новых технологий в различные сферы экономики. Эксперты отметили важность совместной работы государства и бизнеса для достижения поставленных целей. В ближайшие месяцы планируется запуск нескольких пилотных проектов, которые позволят оценить эффективность предложенных решений.",
                "target_length": 200,
                "language": "ru"
            }
        }


class SummarizeResponse(BaseModel):
    """Ответ на суммаризацию"""
    summary: str = Field(..., description="Суммаризированный текст")
    original_length: int = Field(..., description="Длина исходного текста")
    summary_length: int = Field(..., description="Длина саммари")
    compression_ratio: float = Field(..., description="Коэффициент сжатия")
    processing_time: float = Field(..., description="Время обработки в секундах")
    cached: bool = Field(False, description="Было ли взято из кэша")


class ProcessRequest(BaseModel):
    """Запрос на полную обработку (fetch + summarize + paraphrase)"""
    url: Optional[HttpUrl] = Field(None, description="URL новости")
    text: Optional[str] = Field(None, min_length=1, max_length=50000, description="Текст новости")
    platforms: Optional[List[str]] = Field(["telegram", "vk", "instagram"], description="Целевые платформы")
    force_summarize: Optional[bool] = Field(False, description="Принудительная суммаризация")
    target_lengths: Optional[Dict[str, int]] = Field(None, description="Целевые длины для платформ")
    
    @validator('text', 'url')
    def check_input(cls, v, values):
        """Проверка что есть либо url, либо text"""
        if not v and not values.get('url'):
            raise ValueError('Необходимо указать либо url, либо text')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Вчера в центре Москвы открылся новый технологический парк. Мероприятие посетили представители крупнейших IT-компаний и стартапов. На церемонии открытия выступил мэр города, который подчеркнул важность развития инновационных технологий для будущего столицы.",
                "platforms": ["telegram", "vk"],
                "force_summarize": False
            }
        }


class ProcessResponse(BaseModel):
    """Ответ на полную обработку"""
    source: Dict = Field(..., description="Информация об источнике")
    summary: Optional[Dict] = Field(None, description="Суммаризация (если была)")
    paraphrased: Dict = Field(..., description="Парафразированный текст")
    platform_variants: Dict[str, Dict] = Field(..., description="Варианты для платформ")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Семантическая схожесть")
    processing_time: float = Field(..., description="Общее время обработки")
    cached: bool = Field(False, description="Было ли взято из кэша")


class SimilarityRequest(BaseModel):
    """Запрос на проверку схожести"""
    text1: str = Field(..., min_length=1, description="Первый текст")
    text2: str = Field(..., min_length=1, description="Второй текст")
    threshold: Optional[float] = Field(0.75, ge=0.0, le=1.0, description="Порог схожести")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text1": "Сегодня хорошая погода",
                "text2": "Погода сегодня прекрасная",
                "threshold": 0.75
            }
        }


class SimilarityResponse(BaseModel):
    """Ответ на проверку схожести"""
    similarity: float = Field(..., ge=0.0, le=1.0, description="Коэффициент схожести")
    is_similar: bool = Field(..., description="Превышает ли порог")
    threshold: float = Field(..., description="Использованный порог")


class HealthResponse(BaseModel):
    """Ответ health check"""
    status: str = Field(..., description="Статус сервиса (ready/loading/error)")
    model_loaded: bool = Field(..., description="Загружена ли хотя бы одна модель")
    cache_enabled: bool = Field(..., description="Включен ли кэш")
    model_name: Optional[str] = Field(None, description="Имя модели")
    version: str = Field("1.0.0", description="Версия API")
    models_status: Optional[Dict[str, bool]] = Field(None, description="Статус каждой модели")

