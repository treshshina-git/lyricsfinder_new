import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, 
    InlineQuery, 
    InlineQueryResultArticle, 
    InputTextMessageContent
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

# Предполагаем, что ваша функция поиска импортируется так же
from genius import search_song

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# Настройка пагинации: сколько песен выводить за один раз во всплывающем окне
ITEMS_PER_PAGE = 3


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Отправь фрагмент текста песни 🎵\nИли просто введи поисковый запрос!"
    )


# 1. ОБЫЧНЫЙ ЧАТ: Перенаправляем пользователя во всплывающее окно
@dp.message()
async def lyrics_search(message: Message):
    query = message.text.strip()

    # Создаем инлайн-кнопку, которая переключит юзера в инлайн-режим
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"🔍 Найти результаты для '{query}'",
        switch_inline_query=query  # Подставляет текст запроса во всплывающее окно
    )

    await message.answer(
        text=f"Запрос принят! Нажмите кнопку ниже, чтобы открыть всплывающее окно результатов.",
        reply_markup=builder.as_markup()
    )


# 2. ВСПЛЫВАЮЩЕЕ ОКНО: Обработка инлайн-запроса через bot.answer_inline_query
@dp.inline_query()
async def inline_lyrics_search(inline_query: InlineQuery):
    query = inline_query.query.strip()

    # Если пользователь ничего не ввел во всплывающем окне, отдаем пустой список
    if not query:
        await bot.answer_inline_query(
            inline_query_id=inline_query.id,
            results=[],
            is_personal=True
        )
        return

    # Получаем текущее смещение пагинации (offset) от Telegram
    offset = int(inline_query.offset) if inline_query.offset else 0

    # Вызываем вашу функцию поиска из Genius
    # ВАЖНО: Ваша функция должна уметь возвращать список результатов, 
    # либо адаптируйте этот кусок под вашу структуру данных.
    search_results = await search_song(query)

    # Если ничего не найдено
    if not search_results:
        await bot.answer_inline_query(
            inline_query_id=inline_query.id,
            results=[],
            is_personal=True
        )
        return

    # Если search_song возвращает один словарь (как в вашем примере), превращаем его в список.
    # Если он уже возвращает список словарей — эту проверку можно убрать.
    if isinstance(search_results, dict):
        all_items = [search_results]
    else:
        all_items = search_results

    # Пагинация: делаем срез списка под текущую страницу скролла
    start_index = offset
    end_index = offset + ITEMS_PER_PAGE
    page_items = all_items[start_index:end_index]

    results = []
    for item in page_items:
        # Извлекаем данные, которые приходят из вашего модуля genius
        artist = item.get('artist', 'Неизвестный исполнитель')
        title = item.get('title', 'Без названия')
        url = item.get('url', '')
        # Опционально: если Genius отдает обложку трека, можно вытащить её url
        thumbnail = item.get('thumbnail_url', None) 

        results.append(
            InlineQueryResultArticle(
                id=f"song_{item.get('id', start_index)}",  # Уникальный ID для Telegram
                title=f"🎵 {artist} - {title}",
                description="Нажмите, чтобы отправить трек в чат",
                thumbnail_url=thumbnail, # Будет отображаться иконка трека (если есть)
                input_message_content=InputTextMessageContent(
                    message_text=f"🎵 **{artist} — {title}**\n\n Ссылка на Genius: {url}",
                    parse_mode="Markdown"
                )
            )
        )

    # Вычисляем смещение для следующей страницы при скролле вниз
    next_offset = str(end_index) if end_index < len(all_items) else ""

    # КЛЮЧЕВОЙ МЕТОД: Отвечаем во всплывающее окно через bot
    await bot.answer_inline_query(
        inline_query_id=inline_query.id,  # Связываем ответ с запросом юзера
        results=results,                  # Список сформированных статей треков
        next_offset=next_offset,          # Передаем offset для пагинации
        cache_time=1,                     # Минимальный кэш для удобного тестирования
        is_personal=True
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
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
