
#import os
import asyncio
from dotenv import load_dotenv
import telebot
from telebot.types import InlineQueryResultArticle, InputTextMessageContent, ChosenInlineResult
import time
import sys
from genius import search_song
from lrclib_api import get_lyrics

load_dotenv()

BOT_TOKEN = "8802670423:AAG6aZBRd7VHYxgJpoB7oQi0NhuL1IJ8FjQ"
bot = telebot.TeleBot(BOT_TOKEN)

INLINE_CACHE = {}

@bot.inline_handler(lambda q: bool(q.query.strip()))
def inline_search(query):
    try:
        songs = asyncio.run(search_song(query.query.strip()))
    except Exception():
        songs = []

    results = []

    for idx, song in enumerate(songs[:50]):
        result_id = f"{query.from_user.id}:{idx}"
        INLINE_CACHE[result_id] = song

        views = song.get("views", 0)

        text = (
            f"🎵 <b>{song['artist']} - {song['title']}</b>\n"
            f"Нажмите на результат. Полный текст будет отправлен ботом в ЛС."
        )

        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title=f"{song['artist']} - {song['title']}",
                description=f"👁 {views:,}",
                input_message_content=InputTextMessageContent(
                    message_text=text,
                    parse_mode="HTML"
                )
            )
        )

    bot.answer_inline_query(query.id, results, cache_time=10)

@bot.chosen_inline_handler(func=lambda r: True)
def chosen(result: ChosenInlineResult):
    song = INLINE_CACHE.get(result.result_id)
    if not song:
        return

    user_id = result.from_user.id

    try:
        lyrics = asyncio.run(get_lyrics(song["artist"], song["title"]))
    except Exception():
        lyrics = ""

    header = (
        f"🎵 {song['artist']} - {song['title']}\n"
        f"👁 Просмотров: {song.get('views',0):,}\n\n"
    )

    if not lyrics:
        bot.send_message(
            user_id,
            header + f"Текст не найден.\n{song['url']}"
        )
        return

    chunk_size = 3500
    bot.send_message(user_id, header)

    for i in range(0, len(lyrics), chunk_size):
        bot.send_message(user_id, lyrics[i:i+chunk_size])


def main_loop():
    bot.infinity_polling(
        timeout=500,
        long_polling_timeout=1000,
        skip_pending=False
    )
    while 1:
        time.sleep(3)


if __name__ == '__main__':
    try:
        main_loop()
    except KeyboardInterrupt:
        print('\nExiting by user request.\n')
        sys.exit(0)


