"""Конфигурация приложения"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Database
    database_url: str = "postgresql://phoenix_user:password@localhost:5432/phoenix_lab"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # ML Models - Paraphrasing
    paraphrase_model_ru: str = "cointegrated/rut5-base-paraphraser"  # Русская модель
    paraphrase_model_en: str = "google/flan-t5-large"  # Английская модель
    ml_model_name: str = "cointegrated/rut5-base-paraphraser"  # Для обратной совместимости
    ml_model_cache_dir: str = "./models_cache"
    ml_device: str = "cpu"  # cpu или cuda
    ml_max_length: int = 512
    ml_temperature: float = 0.7
    ml_top_p: float = 0.9
    
    # Автоматическая загрузка моделей с Hugging Face
    auto_download_models: bool = True
    
    # Предзагрузка моделей при старте сервера
    preload_models: bool = False
    
    # Summary Models
    summary_model_ru: str = "IlyaGusev/mbart_ru_sum_gazeta"
    summary_model_en: str = "facebook/bart-large-cnn"
    summary_threshold_tokens: int = 1800
    summary_chunk_size: int = 900
    summary_target_length: int = 600
    
    # Similarity Model
    similarity_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    similarity_threshold: float = 0.75
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    
    # Cache
    cache_ttl: int = 604800  # 7 дней
    cache_enabled: bool = True
    
    # Security
    api_key: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

