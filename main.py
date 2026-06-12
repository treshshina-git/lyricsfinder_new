import IPython
# Укажите путь к вашему файлу
file_path = "/mnt/data/lyricsfinder_webapp_ready.zip"

# Создаем интерактивную ссылку для скачивания
IPython.display.FileLink(file_path)

# Combined FastAPI + Aiogram starter
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
async def root():
    return {"status":"ok"}
