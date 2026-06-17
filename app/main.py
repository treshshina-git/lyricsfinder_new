from fastapi import FastAPI, Request
from telegram import Update
from app.bot import setup_app
from app.config import (
    TELEGRAM_BOT_TOKEN,
    WEBHOOK_URL,
    WEBHOOK_SECRET,
    validate_config,
)

app = FastAPI()
tg_app = setup_app()


@app.on_event("startup")
async def startup():
    validate_config()
    await tg_app.initialize()
    await tg_app.bot.set_webhook(
        url=WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET,
    )


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}


@app.get("/health")
def health():
    return {"status": "ok"}

