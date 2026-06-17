from fastapi import FastAPI, Request
from telegram import Update
from app.bot import setup_app
from app.config import (
    TELEGRAM_BOT_TOKEN,
    WEBHOOK_URL,
    WEBHOOK_SECRET,
    validate_config,
)
print("Initializing FastAPI application and Telegram bot...")
app = FastAPI()
tg_app = setup_app()

print("Starting the bot and setting up the webhook...")
@app.on_event("startup")
async def startup():
    validate_config()
    await tg_app.initialize()
    await tg_app.bot.set_webhook(
        url=WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET,
    )

print("Bot is running and webhook is set up.")
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    try:
        update = Update.de_json(data, tg_app.bot)
        # Debug: show which update types Telegram sends (important for inline queries)
        update_dict = update.to_dict()
        print("[webhook] incoming update keys:", list(update_dict.keys()))
        print("[webhook] incoming update:", update_dict)
    except Exception as e:
        print("[webhook] failed to parse update:", repr(e))
        print("[webhook] raw data:", data)
        raise

    await tg_app.process_update(update)
    return {"ok": True}


print("Webhook endpoint is ready to receive updates.")
@app.get("/health")
def health():
    return {"status": "ok"}

print("Health check endpoint is ready.")