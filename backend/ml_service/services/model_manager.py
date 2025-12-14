"""Менеджер ML моделей"""
from typing import Optional
import logging
from config import settings

logger = logging.getLogger(__name__)


class ModelManager:
    """Управление загрузкой и хранением ML моделей"""
    
    def __init__(self):
        self.paraphrase_model = None
        self.paraphrase_tokenizer = None
        self.summary_model = None
        self.summary_tokenizer = None
        self.similarity_model = None
        self._models_loaded = False
    
    def load_paraphrase_model(self):
        """Загрузка модели для парафразирования"""
        if self.paraphrase_model is not None:
            return self.paraphrase_model, self.paraphrase_tokenizer
        
        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            import torch
            
            logger.info(f"Загрузка модели парафразирования: {settings.ml_model_name}")
            
            # Определяем путь к модели
            model_path = f"{settings.ml_model_cache_dir}/flan-t5-large"
            
            # Загрузка токенизатора
            self.paraphrase_tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                local_files_only=True
            )
            
            # Загрузка модели
            self.paraphrase_model = AutoModelForSeq2SeqLM.from_pretrained(
                model_path,
                local_files_only=True
            )
            
            # Перемещение на устройство (CPU или CUDA)
            device = settings.ml_device
            self.paraphrase_model = self.paraphrase_model.to(device)
            self.paraphrase_model.eval()
            
            logger.info("Модель парафразирования загружена успешно")
            return self.paraphrase_model, self.paraphrase_tokenizer
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели парафразирования: {e}")
            raise
    
    def load_summary_model(self, language: str = "ru"):
        """Загрузка модели для суммаризации"""
        if self.summary_model is not None:
            return self.summary_model, self.summary_tokenizer
        
        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            import torch
            
            # Выбор модели в зависимости от языка
            model_name = settings.summary_model_ru if language == "ru" else settings.summary_model_en
            logger.info(f"Загрузка модели суммаризации: {model_name}")
            
            # Определяем путь к модели
            model_path = f"{settings.ml_model_cache_dir}/mbart_ru_sum_gazeta"
            
            # Загрузка токенизатора
            self.summary_tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                local_files_only=True
            )
            
            # Загрузка модели
            self.summary_model = AutoModelForSeq2SeqLM.from_pretrained(
                model_path,
                local_files_only=True
            )
            
            # Перемещение на устройство
            device = settings.ml_device
            self.summary_model = self.summary_model.to(device)
            self.summary_model.eval()
            
            logger.info("Модель суммаризации загружена успешно")
            return self.summary_model, self.summary_tokenizer
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели суммаризации: {e}")
            raise
    
    def load_similarity_model(self):
        """Загрузка модели для проверки схожести"""
        if self.similarity_model is not None:
            return self.similarity_model
        
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info("Загрузка модели схожести")
            
            # Загрузка модели
            self.similarity_model = SentenceTransformer(
                settings.similarity_model,
                cache_folder=settings.ml_model_cache_dir
            )
            
            logger.info("Модель схожести загружена успешно")
            return self.similarity_model
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели схожести: {e}")
            raise
    
    @property
    def models_loaded(self) -> bool:
        """Проверка загружены ли модели"""
        return self.paraphrase_model is not None


# Глобальный экземпляр менеджера моделей
model_manager = ModelManager()


