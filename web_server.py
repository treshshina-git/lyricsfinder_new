import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Количество элементов на одной странице всплывающего окна
ITEMS_PER_PAGE = 5

# Имитация вашего динамического запроса к данным
async def fetch_data_by_query(query: str):
    # Здесь происходит ваш реальный запрос к API или БД по тексту `query`
    # Для примера сгенерируем динамический список из 10 товаров под запрос
    all_results = [
        {"id": f"id_{i}", "title": f"📦 {query.capitalize()} #{i}", "price": f"{1000 * i} руб."}
        for i in range(1, 11)  # Итого 10 динамических элементов
    ]
    return all_results

# Обработчик инлайн-запросов
@dp.inline_query()
async def inline_pagination_handler(inline_query: InlineQuery):
    query_text = inline_query.query.strip()
    
    # Если пользователь ничего не ввел, можно показать пустой список или инструкцию
    if not query_text:
        await inline_query.answer([], is_personal=True)
        return

    # Получаем текущий оффсет (смещение/текущую позицию пагинации)
    # По умолчанию Telegram передает пустую строку "" на первой странице
    offset = int(inline_query.offset) if inline_query.offset else 0

    # Запрашиваем динамические данные по тексту запроса
    all_items = await fetch_data_by_query(query_text)
    
    # Срезаем массив данных под конкретную страницу
    start_index = offset
    end_index = offset + ITEMS_PER_PAGE
    page_items = all_items[start_index:end_index]

    # Формируем список объектов для всплывающего окна
    results = []
    for item in page_items:
        # Кнопка внутри самого товара (опционально)
        builder = InlineKeyboardBuilder()
        builder.button(text="Купить 🛒", callback_data=f"buy_{item['id']}")
        
        results.append(
            InlineQueryResultArticle(
                id=item["id"],
                title=item["title"],
                description=f"Цена: {item['price']}",
                input_message_content=InputTextMessageContent(
                    message_text=f"Вы выбрали:\n**{item['title']}**\nСтоимость: {item['price']}",
                    parse_mode="Markdown"
                ),
                reply_markup=builder.as_markup()
            )
        )

    # Определяем оффсет для следующей страницы
    # Если элементы еще остались, передаем индекс начала следующей страницы.
    # Если это была последняя страница, передаем пустую строку "", чтобы остановить пагинацию.
    next_offset = str(end_index) if end_index < len(all_items) else ""

    # Отправляем ответ во всплывающее окно
    await inline_query.answer(
        results=results,
        next_offset=next_offset,  # Ключевой параметр для пагинации
        cache_time=5,             # Кэширование в секундах (поставьте 0 для тестов)
        is_personal=True          # Результаты уникальны для каждого пользователя
    )

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
