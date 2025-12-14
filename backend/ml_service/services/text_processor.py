"""Сервис для обработки текста (парафразирование, суммаризация)"""
from typing import Optional
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Попытка импортировать transformers (может быть не установлен)
try:
    from transformers import (
        MBartForConditionalGeneration,
        MBartTokenizer,  # Исправлено: MBart50Tokenizer -> MBartTokenizer для mbart_ru_sum_gazeta
        T5ForConditionalGeneration,
        T5Tokenizer,
        AutoModelForSeq2SeqLM,
        AutoTokenizer
    )
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers не установлен. Модели будут работать в режиме заглушек.")


class TextProcessor:
    """Обработка текста: парафразирование и суммаризация"""
    
    def __init__(self):
        """Инициализация процессора"""
        # Модели парафразирования (русская и английская)
        self.paraphrase_model_ru = None
        self.paraphrase_tokenizer_ru = None
        self.paraphrase_model_en = None
        self.paraphrase_tokenizer_en = None
        # Модели суммаризации
        self.summary_model_ru = None
        self.summary_tokenizer_ru = None
        self.summary_model_en = None
        self.summary_tokenizer_en = None
        self.similarity_model = None
        self.models_loaded = False
        # Получаем путь к кэшу из конфига
        from config import settings
        self.models_cache_dir = Path(settings.ml_model_cache_dir)
    
    def _detect_language(self, text: str) -> str:
        """Определение языка текста"""
        try:
            from langdetect import detect
            lang = detect(text)
            # Возвращаем 'ru' или 'en', по умолчанию 'ru'
            return 'ru' if lang == 'ru' else 'en'
        except Exception as e:
            logger.warning(f"Не удалось определить язык: {e}. Используем русский по умолчанию.")
            return 'ru'
    
    def _clean_paraphrased_text(self, text: str) -> str:
        """Очистка результата парафразирования от артефактов
        
        Удаляет:
        - Лишние экранирования кавычек (\")
        - Двойные кавычки в начале/конце
        - Лишние пробелы
        """
        # Убираем экранирование кавычек
        text = text.replace('\\"', '"')
        text = text.replace('\\""', '"')
        
        # Убираем двойные кавычки в начале и конце
        text = text.strip()
        if text.startswith('""') and text.endswith('""'):
            text = text[2:-2]
        elif text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        
        # Убираем множественные пробелы
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # Убираем пробелы перед знаками препинания
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        
        return text.strip()
    
    def _load_paraphrase_model(self, language: str = 'ru'):
        """Загрузка модели для парафразирования
        
        Args:
            language: 'ru' для русского, 'en' для английского
        """
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers не установлен, используется заглушка")
            return None, None
        
        # Проверяем, загружена ли уже нужная модель
        if language == 'ru':
            if self.paraphrase_model_ru is not None:
                return self.paraphrase_model_ru, self.paraphrase_tokenizer_ru
        else:
            if self.paraphrase_model_en is not None:
                return self.paraphrase_model_en, self.paraphrase_tokenizer_en
        
        try:
            from config import settings
            # Выбираем модель в зависимости от языка
            if language == 'ru':
                model_name = settings.paraphrase_model_ru
            else:
                model_name = settings.paraphrase_model_en
            
            # Используем последнюю часть имени модели для папки
            model_folder = model_name.split('/')[-1]
            model_path = self.models_cache_dir / model_folder
            
            logger.info(f"Загрузка модели парафразирования для языка '{language}': {model_name}")
            
            # Проверка наличия модели локально
            config_exists = (model_path / "config.json").exists()
            weights_exist = (model_path / "pytorch_model.bin").exists() or (model_path / "model.safetensors").exists()
            local_model_exists = model_path.exists() and config_exists and weights_exist
            
            if local_model_exists:
                logger.info(f"Загрузка модели из локального кэша: {model_path}")
                # Используем AutoTokenizer для универсальности
                tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
                model = T5ForConditionalGeneration.from_pretrained(str(model_path), local_files_only=True)
            elif settings.auto_download_models:
                # Автоматическая загрузка с Hugging Face
                logger.info(f"Модель не найдена локально. Загрузка с Hugging Face: {model_name}")
                logger.info("Это может занять несколько минут...")
                tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=str(self.models_cache_dir))
                model = T5ForConditionalGeneration.from_pretrained(model_name, cache_dir=str(self.models_cache_dir))
                logger.info("Модель загружена и сохранена в кэш")
            else:
                logger.error(f"Модель не найдена в {model_path} и AUTO_DOWNLOAD_MODELS=False")
                return None, None
            
            # Переводим в режим оценки
            model.eval()
            
            # Оптимизация памяти: отключаем градиенты
            with torch.no_grad():
                # Перемещаем на нужное устройство
                device = settings.ml_device
                if device == "cuda" and torch.cuda.is_available():
                    model = model.to("cuda")
                    # Для CUDA можно использовать float16 для экономии памяти
                    try:
                        model = model.half()
                    except:
                        pass  # Если не поддерживается, оставляем как есть
            
            # Сохраняем модель в соответствующую переменную
            if language == 'ru':
                self.paraphrase_model_ru = model
                self.paraphrase_tokenizer_ru = tokenizer
            else:
                self.paraphrase_model_en = model
                self.paraphrase_tokenizer_en = tokenizer
            
            # Очистка памяти после загрузки
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info(f"Модель парафразирования ({language}) загружена успешно")
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели парафразирования: {str(e)}")
            return None, None
    
    async def paraphrase(
        self,
        text: str,
        max_length: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        num_beams: int = 5
    ) -> str:
        """
        Парафразирование текста
        
        Автоматически определяет язык и использует соответствующую модель:
        - Русский: cointegrated/rut5-base-paraphraser
        - Английский: google/flan-t5-large
        """
        if TRANSFORMERS_AVAILABLE:
            # Определяем язык текста
            language = self._detect_language(text)
            logger.info(f"Определён язык: {language}")
            
            # Загружаем соответствующую модель
            model, tokenizer = self._load_paraphrase_model(language)
            
            if model is not None and tokenizer is not None:
                try:
                    from config import settings
                    
                    # Формируем промпт в зависимости от модели
                    if language == 'ru':
                        # Для русской модели rut5-base-paraphraser не нужен префикс
                        prompt = text
                    else:
                        # Для английской модели flan-t5-large используем префикс
                        prompt = f"paraphrase: {text}"
                    
                    # Токенизация
                    inputs = tokenizer(
                        prompt,
                        max_length=512,
                        truncation=True,
                        padding=True,
                        return_tensors="pt"
                    )
                    
                    # Перемещаем на нужное устройство
                    device = settings.ml_device
                    if device == "cuda" and torch.cuda.is_available():
                        inputs = {k: v.to("cuda") for k, v in inputs.items()}
                    
                    # Генерация
                    with torch.no_grad():
                        outputs = model.generate(
                            **inputs,
                            max_length=max_length,
                            num_beams=num_beams,
                            temperature=temperature,
                            top_p=top_p,
                            early_stopping=True,
                            do_sample=True
                        )
                    
                    # Декодирование
                    paraphrased = tokenizer.decode(outputs[0], skip_special_tokens=True)
                    
                    # Постобработка: удаление лишних экранирований и чистка
                    paraphrased = self._clean_paraphrased_text(paraphrased)
                    
                    return paraphrased
                    
                except Exception as e:
                    logger.error(f"Ошибка при парафразировании: {str(e)}")
                    # Fallback на заглушку
        
        # Заглушка если модель не загружена
        return f"[Парафраз] {text}"
    
    def _load_summary_model_ru(self):
        """Загрузка модели для суммаризации на русском"""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers не установлен, используется заглушка")
            return None, None
        
        if self.summary_model_ru is not None:
            return self.summary_model_ru, self.summary_tokenizer_ru
        
        try:
            from config import settings
            model_path = self.models_cache_dir / "mbart_ru_sum_gazeta"
            
            # Проверка наличия модели локально
            local_model_exists = model_path.exists() and (model_path / "pytorch_model.bin").exists()
            
            if local_model_exists:
                logger.info(f"Загрузка модели из локального кэша: {model_path}")
                # Проверяем наличие всех необходимых файлов
                required_files = ["pytorch_model.bin", "config.json", "tokenizer_config.json"]
                missing_files = [f for f in required_files if not (model_path / f).exists()]
                if missing_files:
                    logger.warning(f"Отсутствуют файлы модели: {missing_files}. Попробуем загрузить с Hugging Face.")
                    local_model_exists = False
                else:
                    # Используем AutoTokenizer для автоматического определения правильного класса токенизатора
                    logger.info("Загрузка токенизатора...")
                    tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
                    logger.info("Токенизатор загружен. Загрузка модели (это может занять время, модель ~2-3 GB)...")
                    # Загружаем модель с ignore_mismatched_sizes=False для строгой проверки
                    # ВАЖНО: Используем use_safetensors=False чтобы загрузить pytorch_model.bin, а не safetensors
                    model = MBartForConditionalGeneration.from_pretrained(
                        str(model_path), 
                        local_files_only=True,
                        ignore_mismatched_sizes=False,
                        use_safetensors=False  # Принудительно используем pytorch_model.bin
                    )
                    logger.info("Модель загружена из кэша")
            elif settings.auto_download_models:
                # Автоматическая загрузка с Hugging Face
                logger.info("Модель не найдена локально. Загрузка с Hugging Face: IlyaGusev/mbart_ru_sum_gazeta")
                logger.info("Это может занять несколько минут...")
                model_name = "IlyaGusev/mbart_ru_sum_gazeta"
                # Используем AutoTokenizer для автоматического определения правильного класса токенизатора
                logger.info("Скачивание токенизатора...")
                tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=str(self.models_cache_dir))
                logger.info("Токенизатор скачан. Скачивание модели (~2-3 GB, это может занять время)...")
                # ВАЖНО: Используем use_safetensors=False для совместимости
                model = MBartForConditionalGeneration.from_pretrained(
                    model_name, 
                    cache_dir=str(self.models_cache_dir),
                    use_safetensors=False
                )
                logger.info("Модель скачана и сохранена в кэш")
            else:
                logger.error(f"Модель не найдена в {model_path} и AUTO_DOWNLOAD_MODELS=False")
                return None, None
            
            # Переводим в режим оценки
            logger.info("Перевод модели в режим оценки...")
            model.eval()
            logger.info("Модель переведена в режим оценки")
            
            # Оптимизация памяти: отключаем градиенты и перемещаем на устройство
            with torch.no_grad():
                device = settings.ml_device
                if device == "cuda" and torch.cuda.is_available():
                    model = model.to("cuda")
                    # Для CUDA можно использовать float16 для экономии памяти
                    try:
                        model = model.half()
                    except:
                        pass  # Если не поддерживается, оставляем как есть
            
            # Проверка: пробуем закодировать/декодировать тестовый текст
            try:
                logger.info("Тестирование токенизатора...")
                test_text = "Тест"
                with torch.no_grad():
                    test_inputs = tokenizer(test_text, return_tensors="pt")
                    test_decoded = tokenizer.decode(test_inputs["input_ids"][0], skip_special_tokens=True)
                logger.info(f"Токенизатор работает корректно. Тестовый текст '{test_text}' -> '{test_decoded}'")
            except Exception as e:
                logger.warning(f"Предупреждение при тестировании токенизатора: {e}")
            
            logger.info("Сохранение модели в память...")
            self.summary_model_ru = model
            self.summary_tokenizer_ru = tokenizer
            
            # Очистка памяти после загрузки
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info("✅ Модель суммаризации загружена успешно")
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели суммаризации: {str(e)}")
            return None, None
    
    async def summarize(
        self,
        text: str,
        target_length: Optional[int] = None,
        language: Optional[str] = None
    ) -> str:
        """
        Суммаризация текста
        
        Использует mbart_ru_sum_gazeta для русского языка
        """
        # Определение языка
        if language is None:
            language = "ru"  # По умолчанию русский
        
        # Если русский язык и transformers доступен - используем реальную модель
        if language == "ru" and TRANSFORMERS_AVAILABLE:
            logger.info("Загрузка модели для сокращения текста...")
            model, tokenizer = self._load_summary_model_ru()
            
            if model is not None and tokenizer is not None:
                try:
                    logger.info("Подготовка текста к обработке...")
                    # Настройка языка для MBart (если токенизатор поддерживает)
                    # Модель mbart_ru_sum_gazeta уже обучена на русском, но может требовать языковую настройку
                    if hasattr(tokenizer, 'src_lang'):
                        # Устанавливаем русский язык как исходный
                        tokenizer.src_lang = "ru_RU"
                    
                    logger.info("Разбиение текста на токены...")
                    # Токенизация с правильной настройкой языка
                    inputs = tokenizer(
                        text,
                        max_length=1024,
                        truncation=True,
                        padding=True,
                        return_tensors="pt"
                    )
                    
                    # Для MBart моделей нужно добавить языковой токен в decoder_input_ids
                    # Но для mbart_ru_sum_gazeta это может быть не нужно, так как модель уже специализирована
                    # Проверяем, есть ли метод для установки целевого языка
                    if hasattr(tokenizer, 'tgt_lang'):
                        tokenizer.tgt_lang = "ru_RU"
                    
                    # Генерация саммари
                    # Преобразуем target_length из символов в примерное количество токенов (1 токен ≈ 4 символа)
                    # Добавляем запас, чтобы модель могла закончить предложение
                    max_tokens = int((target_length or 200) * 1.5) if target_length else 300
                    min_tokens = max(30, int((target_length or 200) * 0.3)) if target_length else 50
                    
                    logger.info(f"Генерация сокращенного текста (это может занять 10-30 секунд)...")
                    with torch.no_grad():
                        # Для MBart может потребоваться decoder_start_token_id
                        generate_kwargs = {
                            "input_ids": inputs["input_ids"],
                            "max_length": max_tokens,
                            "min_length": min_tokens,
                            "num_beams": 4,
                            "early_stopping": True,
                            "length_penalty": 1.2,
                            "no_repeat_ngram_size": 3,
                            "do_sample": False
                        }
                        
                        # Добавляем decoder_start_token_id если токенизатор его поддерживает
                        if hasattr(tokenizer, 'lang_code_to_id') and hasattr(tokenizer, 'tgt_lang'):
                            try:
                                decoder_start_token_id = tokenizer.lang_code_to_id.get(tokenizer.tgt_lang, tokenizer.eos_token_id)
                                generate_kwargs["decoder_start_token_id"] = decoder_start_token_id
                            except:
                                pass
                        
                        summary_ids = model.generate(**generate_kwargs)
                    
                    logger.info("Преобразование результата в текст...")
                    # Декодирование
                    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
                    
                    # Проверка на мусор: если в результате есть нечитаемые символы - возвращаем ошибку
                    if not summary or len(summary.strip()) < 10:
                        logger.warning("Модель вернула пустой или слишком короткий результат")
                        raise ValueError("Модель вернула некорректный результат")
                    
                    # Постобработка: обрезаем до последнего законченного предложения
                    summary = self._trim_to_complete_sentence(summary, target_length)
                    
                    return summary
                    
                except Exception as e:
                    logger.error(f"Ошибка при суммаризации: {str(e)}")
                    # Fallback на заглушку
        
        # Заглушка если модель не загружена или другой язык
        if target_length:
            return text[:target_length] + "..."
        return text[:600] + "..."
    
    def _trim_to_complete_sentence(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Обрезает текст до последнего законченного предложения
        
        Ищет последнюю точку, восклицательный или вопросительный знак
        и обрезает текст до этого места, чтобы не было обрыва на середине предложения
        """
        if not text:
            return text
        
        # Если текст уже короче целевой длины - возвращаем как есть
        if max_length and len(text) <= max_length:
            # Проверяем, заканчивается ли текст на знак препинания
            if text.rstrip().endswith(('.', '!', '?', '…')):
                return text.strip()
        
        # Если нужно обрезать - ищем последнее законченное предложение
        if max_length and len(text) > max_length:
            # Ищем последний знак препинания в пределах целевой длины
            search_text = text[:max_length + 50]  # Небольшой запас для поиска
            last_period = search_text.rfind('.')
            last_exclamation = search_text.rfind('!')
            last_question = search_text.rfind('?')
            last_ellipsis = search_text.rfind('…')
            
            # Находим последний знак препинания
            last_punctuation = max(last_period, last_exclamation, last_question, last_ellipsis)
            
            if last_punctuation > max_length * 0.5:  # Если знак препинания не слишком близко к началу
                # Обрезаем до знака препинания включительно
                return text[:last_punctuation + 1].strip()
            else:
                # Если не нашли подходящий знак - обрезаем до целевой длины
                # и пытаемся найти хотя бы какой-то знак препинания
                trimmed = text[:max_length]
                # Ищем любой знак препинания в последних 100 символах
                for i in range(len(trimmed) - 1, max(0, len(trimmed) - 100), -1):
                    if trimmed[i] in '.!?…':
                        return trimmed[:i + 1].strip()
                return trimmed.strip()
        
        # Если не нужно обрезать по длине, но текст не заканчивается на знак препинания
        # - ищем последний знак препинания и обрезаем до него
        text_stripped = text.rstrip()
        if not text_stripped.endswith(('.', '!', '?', '…')):
            # Ищем последний знак препинания
            last_period = text.rfind('.')
            last_exclamation = text.rfind('!')
            last_question = text.rfind('?')
            last_ellipsis = text.rfind('…')
            
            last_punctuation = max(last_period, last_exclamation, last_question, last_ellipsis)
            
            if last_punctuation > len(text) * 0.5:  # Если знак препинания не слишком близко к началу
                return text[:last_punctuation + 1].strip()
        
        return text.strip()
    
    async def check_similarity(self, text1: str, text2: str) -> float:
        """
        Проверка семантической схожести
        
        TODO: Реальная реализация через sentence-transformers
        Пока возвращает заглушку
        """
        # Заглушка - возвращает фиксированное значение
        # В реальной реализации здесь будет загрузка модели и вычисление схожести
        return 0.85

