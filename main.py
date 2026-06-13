from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import CallbackQuery, Message, InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram import F, Bot, Dispatcher
from aiogram.filters import CommandStart
from dotenv import load_dotenv
import asyncio
import os

from genius import search_song
from lrclib_api import get_lyrics
from utils import split_text
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo
)

import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
search_cache = {}
load_dotenv()
dp = Dispatcher()


@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_user_query(message):
    # Игнорируем команды вроде /start
    if message.text.startswith('/'):
        return
        
    query_text = message.text.strip()
    
    # Создаем клавиатуру с кнопкой переключения в инлайн
    markup = types.InlineKeyboardMarkup()
    switch_button = types.InlineKeyboardButton(
        text=f"🔍 Показать результаты для '{query_text}'",
        switch_inline_query=query_text  # Переводит в инлайн-режим с этим текстом
    )
    markup.add(switch_button)
    
    bot.send_message(
        chat_id=message.chat.id,
        text=f"Запрос «{query_text}» принят! Нажмите на кнопку ниже, чтобы открыть всплывающее окно с пагинацией.",
        reply_markup=markup
    )
@bot.inline_handler(func=lambda query: True)
def inline_pagination_handler(inline_query):
    query_text = inline_query.query.strip()
    
    # Если поле ввода пустое, отправляем пустой список
    if not query_text:
        bot.answer_inline_query(
            inline_query_id=inline_query.id, 
            results=[], 
            cache_time=1,
            is_personal=True
        )
        return

    # Получаем текущее смещение (offset) для пагинации
    # В telebot это строка, поэтому безопасно переводим в int
    offset = int(inline_query.offset) if inline_query.offset else 0

    # Запрашиваем динамические данные
    all_items = fetch_data_by_query(query_text)
    
    # Срез списка под текущую страницу (например, с 0 по 3, затем с 3 по 6 и т.д.)
    start_index = offset
    end_index = offset + ITEMS_PER_PAGE
    page_items = all_items[start_index:end_index]

    results = []
    for item in page_items:
        # Формируем элемент для всплывающего списка
        article = types.InlineQueryResultArticle(
            id=item["id"],
            title=item["title"],
            description=f"Цена: {item['price']}",
            input_message_content=types.InputTextMessageContent(
                message_text=f"Вы выбрали:\n*{item['title']}*\nСтоимость: {item['price']}",
                parse_mode="Markdown"
            )
        )
        results.append(article)

    # Вычисляем offset для загрузки следующей страницы при скролле
    next_offset = str(end_index) if end_index < len(all_items) else ""

    # Отправляем результаты во всплывающее инлайн-окно
    bot.answer_inline_query(
        inline_query_id=inline_query.id,  # Указываем ID инлайн-запроса
        results=results,                  # Список объектов InlineQueryResultArticle
        next_offset=next_offset,          # Смещение для пагинации (авто-запрос при скролле)
        cache_time=1,                     # Минимальное кэширование для тестов
        is_personal=True                  # Ответ индивидуален для каждого юзера
    )


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
    await message.answer(
    "Открыть поиск",
    reply_markup=kb
    )


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


@dp.inline_query(F.data == "noop")
async def noop(inline_query: InlineQuery):
    await inline_query.answer()





@dp.inline_query(F.data.startswith("song_"))
async def select_song(inline_query: InlineQuery):

    index = int(inline_query.data.replace("song_", ""))

    songs = search_cache.get(inline_query.from_user.id)

    if not songs:
        await inline_query.answer("Поиск устарел", show_alert=True)
        return

    song = songs[index]

    artist = song["artist"]
    title = song["title"]
    url = song["url"]

    await inline_query.answer()

    await inline_query.message.answer(
        f"🔍 Получаю текст:\n{artist} - {title}"
    )

    lyrics = await get_lyrics(artist, title)

    if not lyrics:
        await inline_query.message.answer(
            f"🎵 {artist} - {title}\n\n"
            f"Текст не найден в LRCLIB.\n\n"
            f"🔗 {url}"
        )
        return

    await inline_query.message.answer(
        f"🎵 {artist} - {title}\n"
        f"👁 Просмотров на Genius: {song.get('views', 0):,}"
    )

    for part in split_text(lyrics):
        await inline_query.message.answer(part)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
