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
    
