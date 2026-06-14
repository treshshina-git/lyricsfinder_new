
import os, sys, html, asyncio, time
from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from genius import search_song
from lrclib_api import get_lyrics

load_dotenv()
BOT_TOKEN=os.getenv("BOT_TOKEN")
bot = AsyncTeleBot(BOT_TOKEN)

SEARCH_CACHE = {}
LYRICS_CACHE = {}
TTL_SEARCH = 600
TTL_LYRICS = 21600

async def cached_search(q):
    now=time.time()
    if q in SEARCH_CACHE and now-SEARCH_CACHE[q][0] < TTL_SEARCH:
        return SEARCH_CACHE[q][1]
    data = await search_song(q)
    SEARCH_CACHE[q]=(now,data)
    return data

async def cached_lyrics(a,t):
    key=f"{a}|{t}"
    now=time.time()
    if key in LYRICS_CACHE and now-LYRICS_CACHE[key][0] < TTL_LYRICS:
        return LYRICS_CACHE[key][1]
    lyr = await get_lyrics(a,t)
    LYRICS_CACHE[key]=(now,lyr)
    return lyr

@bot.inline_handler(func=lambda q: len(q.query.strip())>1)
async def inline_query(query):
    songs = await cached_search(query.query.strip())
    tasks=[cached_lyrics(s['artist'],s['title']) for s in songs[:20]]
    lyrics_list=await asyncio.gather(*tasks, return_exceptions=True)

    results=[]
    for i,(song,lyrics) in enumerate(zip(songs[:20],lyrics_list)):
        if isinstance(lyrics,Exception) or not lyrics:
            lyrics="Текст не найден."
        text=f"🎵 <b>{html.escape(song['artist'])} - {html.escape(song['title'])}</b>\n\n{html.escape(lyrics[:3900])}"
        results.append(types.InlineQueryResultArticle(
            id=str(i),
            title=f"{song['artist']} - {song['title']}",
            description="Отправить текст песни",
            input_message_content=types.InputTextMessageContent(text, parse_mode="HTML")
        ))
    await bot.answer_inline_query(query.id, results, cache_time=30, is_personal=True)


if __name__ == "__main__":
    asyncio.run(
        bot.infinity_polling(
            skip_pending=True
        )
    )
