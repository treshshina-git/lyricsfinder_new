import os
import requests
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, InlineQueryHandler, ContextTypes

BOT_TOKEN = os.environ["BOT_TOKEN"]
GENIUS_TOKEN = os.environ["GENIUS_TOKEN"]

def search_genius(query: str):
    url = "https://api.genius.com/search"
    headers = {"Authorization": f"Bearer {GENIUS_TOKEN}"}
    r = requests.get(url, headers=headers, params={"q": query}, timeout=15)
    r.raise_for_status()

    hits = r.json().get("response", {}).get("hits", [])
    results = []

    for hit in hits[:10]:
        song = hit["result"]
        title = song.get("title", "Unknown")
        artist = song.get("primary_artist", {}).get("name", "Unknown")
        song_url = song.get("url", "")

        text = f"🎵 {title}\n👤 {artist}\n🔗 {song_url}"

        results.append(
            InlineQueryResultArticle(
                id=str(song["id"]),
                title=title,
                description=artist,
                input_message_content=InputTextMessageContent(text),
            )
        )

    return results

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()

    if not query:
        return

    try:
        results = search_genius(query)
        await update.inline_query.answer(
            results=results,
            cache_time=5,
            is_personal=True
        )
    except Exception as e:
        print("ERROR:", e)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(InlineQueryHandler(inline_query))
    app.run_polling()

if __name__ == "__main__":
    main()