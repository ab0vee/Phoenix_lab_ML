"""Скрипт для тестирования загруженных моделей"""
import asyncio
from services.model_manager import model_manager
from services.text_processor import TextProcessor
from config import settings

print("=" * 60)
print("Тестирование ML моделей Phoenix LAB")
print("=" * 60)

async def test_models():
    """Тест загрузки и работы моделей"""
    processor = TextProcessor()
    
    # Тест 1: Парафразирование
    print("\n1. Тест парафразирования (flan-t5-large):")
    print("-" * 60)
    test_text = "Сегодня произошло важное событие в мире технологий."
    print(f"Исходный текст: {test_text}")
    
    try:
        paraphrased = await processor.paraphrase(test_text)
        print(f"Парафраз: {paraphrased}")
        print("✓ Парафразирование работает")
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    
    # Тест 2: Суммаризация
    print("\n2. Тест суммаризации (mbart_ru_sum_gazeta):")
    print("-" * 60)
    long_text = """
    Сегодня в столице прошло важное событие. Президент встретился с представителями
    ведущих технологических компаний для обсуждения перспектив развития отрасли.
    На встрече были представлены новые проекты в области искусственного интеллекта
    и машинного обучения. Эксперты отметили, что внедрение новых технологий позволит
    значительно улучшить качество жизни граждан и повысить конкурентоспособность
    экономики на мировом рынке.
    """
    print(f"Длинный текст: {len(long_text)} символов")
    
    try:
        summary = await processor.summarize(long_text.strip())
        print(f"Саммари: {summary}")
        print(f"Длина саммари: {len(summary)} символов")
        print("✓ Суммаризация работает")
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    
    # Тест 3: Проверка схожести
    print("\n3. Тест проверки схожести:")
    print("-" * 60)
    text1 = "Сегодня хорошая погода"
    text2 = "Погода сегодня прекрасная"
    
    try:
        similarity = await processor.check_similarity(text1, text2)
        print(f"Текст 1: {text1}")
        print(f"Текст 2: {text2}")
        print(f"Схожесть: {similarity:.3f}")
        print("✓ Проверка схожести работает")
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    
    # Информация о моделях
    print("\n" + "=" * 60)
    print("Информация о загруженных моделях:")
    print(f"Устройство: {settings.ml_device}")
    print(f"Кэш моделей: {settings.ml_model_cache_dir}")
    print(f"Модели загружены: {model_manager.models_loaded}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_models())


