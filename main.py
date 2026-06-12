from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import CallbackQuery, Message
from aiogram import F, Bot, Dispatcher
from aiogram.filters import CommandStart
from dotenv import load_dotenv

import asyncio
import os

from genius import search_song
from lrclib_api import get_lyrics
from utils import split_text

search_cache = {}

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


def build_page(songs, page=0, per_page=5):
    builder = InlineKeyboardBuilder()

    start = page * per_page
    end = start + per_page

    page_songs = songs[start:end]

    for index, song in enumerate(page_songs, start=start):
        views = song.get("views", 0)

        if views >= 1_000_000:
            views_text = f"{views // 1_000_000}M"
        elif views >= 1_000:
            views_text = f"{views // 1_000}K"
        else:
            views_text = str(views)

        builder.button(
            text=f"🎵 {song['artist'][:20]} - {song['title'][:20]} | 👁 {views_text}",
            callback_data=f"song_{index}"
        )

    total_pages = (len(songs) - 1) // per_page + 1

    nav = []

    if page > 0:
        nav.append(("⬅️", f"page_{page - 1}"))

    nav.append((f"{page + 1}/{total_pages}", "noop"))

    if end < len(songs):
        nav.append(("➡️", f"page_{page + 1}"))

    for text, data in nav:
        builder.button(
            text=text,
            callback_data=data
        )

    builder.adjust(*([1] * len(page_songs)), len(nav))

    return builder


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("🎵 Отправьте название песни или строку из песни.")


@dp.message()
async def find_song(message: Message):

    query = message.text.strip()

    if len(query) > 200:
        await message.answer("Слишком длинный запрос.")
        return

    await message.answer("🔍 Ищу песню...")

    songs = await search_song(query)

    if not songs:
        await message.answer("❌ Ничего не найдено")
        return

    search_cache[message.from_user.id] = songs

    builder = build_page(songs, page=0)

    await message.answer(
        "🎵 Выберите песню:",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery):
    await callback.answer()


@dp.callback_query(F.data.startswith("page_"))
async def page_change(callback: CallbackQuery):

    page = int(callback.data.replace("page_", ""))

    songs = search_cache.get(callback.from_user.id)

    if not songs:
        await callback.answer("Поиск устарел", show_alert=True)
        return

    builder = build_page(songs, page=page)

    await callback.message.edit_reply_markup(
        reply_markup=builder.as_markup()
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("song_"))
async def select_song(callback: CallbackQuery):

    index = int(callback.data.replace("song_", ""))

    songs = search_cache.get(callback.from_user.id)

    if not songs:
        await callback.answer("Поиск устарел", show_alert=True)
        return

    song = songs[index]

    artist = song["artist"]
    title = song["title"]
    url = song["url"]

    await callback.answer()

    await callback.message.answer(
        f"🔍 Получаю текст:\n{artist} - {title}"
    )

    lyrics = await get_lyrics(artist, title)

    if not lyrics:
        await callback.message.answer(
            f"🎵 {artist} - {title}\n\n"
            f"Текст не найден в LRCLIB.\n\n"
            f"🔗 {url}"
        )
        return

    await callback.message.answer(
        f"🎵 {artist} - {title}\n"
        f"👁 Просмотров на Genius: {song.get('views', 0):,}"
    )

    for part in split_text(lyrics):
        await callback.message.answer(part)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
