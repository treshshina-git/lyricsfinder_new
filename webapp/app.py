
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
app=FastAPI()
@app.get("/", response_class=HTMLResponse)
async def home():
    return open("webapp/templates/index.html",encoding="utf-8").read()
