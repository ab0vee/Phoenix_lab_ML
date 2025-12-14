from huggingface_hub import hf_hub_download

path = hf_hub_download(repo_id="google/flan-t5-large", filename="pytorch_model.bin")
print("Файл скачан сюда:", path)