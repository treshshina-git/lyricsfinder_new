
import os
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, InlineQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

NEWS_SOURCES = {
    "BBC": "https://www.bbc.com/news",
    "Reuters": "https://www.reuters.com/world/",
    "DW": "https://www.dw.com/en/top-stories/s-9097"
}

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = (update.inline_query.query or "").strip()
    if not query:
        return

    results = []
    for name, url in NEWS_SOURCES.items():
        headlines = []
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent":"Mozilla/5.0"})
            soup = BeautifulSoup(r.text, "html.parser")
            for h in soup.find_all(["h1","h2","h3"])[:5]:
                text = h.get_text(" ", strip=True)
                if text:
                    headlines.append(text)
        except Exception as e:
            headlines.append(f"Error: {e}")

        message = "\n".join([f"• {x}" for x in headlines[:5]])
        results.append(
            InlineQueryResultArticle(
                id=name,
                title=name,
                description=f"Show latest headlines from {name}",
                input_message_content=InputTextMessageContent(
                    f"📰 {name}\n\n{message}"
                )
            )
        )

    await update.inline_query.answer(results, cache_time=10)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(InlineQueryHandler(inline_query))
    app.run_polling()

if __name__ == "__main__":
    main()
