import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
VK_CLIENT_ID = os.getenv("VK_CLIENT_ID")
VK_CLIENT_SECRET = os.getenv("VK_CLIENT_SECRET")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
CHAT_RULETTE_CATEGORY_ID = os.getenv("DEFAULT_CATEGORY_ID")
TOKEN_VK_URL = os.getenv("TOKEN_VK_URL")
API_URL_STREAMS = os.getenv("API_URL_STREAMS")
API_URL_SECTIONS = os.getenv("API_URL_SECTIONS")
print("Configuration loaded:")
def validate_config():
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")

    if not VK_CLIENT_ID:
        missing.append("VK_CLIENT_ID")

    if not VK_CLIENT_SECRET:
        missing.append("VK_CLIENT_SECRET")

    if not WEBHOOK_URL:
        missing.append("WEBHOOK_URL")

    if missing:
        raise RuntimeError(
            f"Missing env vars: {', '.join(missing)}"
        )

print("Configuration validation completed. All required environment variables are set.")