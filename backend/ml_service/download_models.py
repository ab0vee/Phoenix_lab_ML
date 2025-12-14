"""Скрипт для загрузки ML моделей"""
from huggingface_hub import snapshot_download
import os

# Директория для кэша моделей
cache_dir = "./models_cache"
os.makedirs(cache_dir, exist_ok=True)

print("Начало загрузки моделей...")

# 1. Модель для суммаризации (русский язык)
print("\n1. Загрузка mbart_ru_sum_gazeta для суммаризации...")
try:
    model_path = snapshot_download(
        repo_id="IlyaGusev/mbart_ru_sum_gazeta",
        cache_dir=cache_dir,
        local_dir=f"{cache_dir}/mbart_ru_sum_gazeta",
        local_dir_use_symlinks=False
    )
    print(f"✓ mbart_ru_sum_gazeta загружена: {model_path}")
except Exception as e:
    print(f"✗ Ошибка при загрузке mbart_ru_sum_gazeta: {e}")

# 2. Модель для парафразирования (flan-t5-large)
print("\n2. Загрузка flan-t5-large для парафразирования...")
try:
    model_path = snapshot_download(
        repo_id="google/flan-t5-large",
        cache_dir=cache_dir,
        local_dir=f"{cache_dir}/flan-t5-large",
        local_dir_use_symlinks=False
    )
    print(f"✓ flan-t5-large загружена: {model_path}")
except Exception as e:
    print(f"✗ Ошибка при загрузке flan-t5-large: {e}")

# 3. Модель для проверки схожести
print("\n3. Загрузка sentence-transformers для проверки схожести...")
try:
    model_path = snapshot_download(
        repo_id="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        cache_dir=cache_dir,
        local_dir=f"{cache_dir}/sentence-transformers",
        local_dir_use_symlinks=False
    )
    print(f"✓ sentence-transformers загружена: {model_path}")
except Exception as e:
    print(f"✗ Ошибка при загрузке sentence-transformers: {e}")

print("\nГотово! Модели сохранены в:", os.path.abspath(cache_dir))


