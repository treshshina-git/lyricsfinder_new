from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    InlineQueryHandler,
    CommandHandler,
)

from app.config import TELEGRAM_BOT_TOKEN
from app.vk_api import get_online_sections, get_online_streams


MENU_PREFIX = "menu"
print("Bot module loaded. Ready to set up handlers and build the menu.")

def _parse_query(q: str) -> dict:
    parts = (q or "").strip().split(":")
    if len(parts) < 2 or parts[0] != MENU_PREFIX:
        return {"type": "unknown"}

    if parts[1] == "sections":
        page = 0
        if len(parts) >= 3 and parts[2].isdigit():
            page = int(parts[2])
        return {"type": "sections", "page": page}

    if parts[1] == "streams" and len(parts) >= 3:
        section_id = parts[2]
        page = 0
        if len(parts) >= 4 and parts[3].isdigit():
            page = int(parts[3])
        return {"type": "streams", "section_id": section_id, "page": page}

    return {"type": "unknown"}


def _btn_switch(query: str, text: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text,
        switch_inline_query_current_chat=query,
    )


def build_sections_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    sections = get_online_sections()
    sections.sort(key=lambda x: x.get("viewers", 0), reverse=True)
    for sec in sections:
        if sec.get("name"):
            sec["name"] = sec["name"][:30]

    page_size = 5
    start = page * page_size
    items = sections[start : start + page_size]

    keyboard_rows = [
        [
            InlineKeyboardButton(
                sec["name"],
                switch_inline_query_current_chat=f"{MENU_PREFIX}:streams:{sec['id']}:{0}",
            )
        ]
        for sec in items
    ]

    prev_page = max(page - 1, 0)
    next_page = page + 1

    keyboard_rows.append(
        [
            InlineKeyboardButton(
                "◀ Назад",
                switch_inline_query_current_chat=f"{MENU_PREFIX}:sections:{prev_page}",
            ),
            InlineKeyboardButton(
                "Вперёд ▶",
                switch_inline_query_current_chat=f"{MENU_PREFIX}:sections:{next_page}",
            ),
        ]
    )

    keyboard_rows.append(
        [
            _btn_switch(f"{MENU_PREFIX}:sections:0", "🏠 В начало"),
        ]
    )

    return InlineKeyboardMarkup(keyboard_rows)


def build_streams_keyboard(section_id: str, page: int = 0) -> InlineKeyboardMarkup:
    update_query = f"{MENU_PREFIX}:streams:{section_id}:{page}"
    start_query = f"{MENU_PREFIX}:sections:0"

    prev_page = max(page - 1, 0)
    next_page = page + 1

    rows = [
        [
            _btn_switch(update_query, "🔄 Обновить"),
            _btn_switch(start_query, "🏠 В начало"),
        ],
        [
            InlineKeyboardButton(
                "◀ Назад",
                switch_inline_query_current_chat=f"{MENU_PREFIX}:streams:{section_id}:{prev_page}",
            ),
            InlineKeyboardButton(
                "Вперёд ▶",
                switch_inline_query_current_chat=f"{MENU_PREFIX}:streams:{section_id}:{next_page}",
            ),
        ],
    ]
    return InlineKeyboardMarkup(rows)


def format_sections_for_text(sections: list[dict]) -> str:
    lines = []
    for sec in sections:
        name = sec.get("name", "")
        viewers = sec.get("viewers", 0)
        lines.append(f"• {name} — 👥 {viewers}")
    return "\n".join(lines) if lines else "Нет активных разделов."


def format_streams_for_text(streams: list[dict]) -> str:
    return "🌕🌕🌕🌕🌕🌕🌕🌕🌕🌕🌕🌕🌕🌕\n\n".join(
        (
            f"📺 <b>{s.get('owner','unknown')}</b> 📺 \n"
            f"{s.get('title','No title')}\n"
            f"🕶️ {s.get('viewers', 0)}              🔗<a href='{s.get('url','')}'>ссылка</a>🔗\n"
        )
        for s in streams
    )


async def inline_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    iq = update.inline_query
    if iq is None:
        return

    req = _parse_query(iq.query)

    from telegram import InlineQueryResultArticle

    if req["type"] == "unknown":
        context_str = "Неверный запрос меню."
        await iq.answer(
            results=[
                InlineQueryResultArticle(
                    id="unknown",
                    title="Неверный запрос",
                    input_message_content={
                        "message_text": context_str,
                        "parse_mode": "HTML",
                    },
                )
            ],
            cache_time=1,
        )
        return

    if req["type"] == "sections":
        page = req["page"]

        sections = get_online_sections()
        sections.sort(key=lambda x: x.get("viewers", 0), reverse=True)
        for sec in sections:
            if sec.get("name"):
                sec["name"] = sec["name"][:30]

        page_size = 5
        start = page * page_size
        items = sections[start : start + page_size]

        text = "<b>Выберите раздел:</b>\n\n" + format_sections_for_text(items)
        keyboard = build_sections_keyboard(page=page)

        await iq.answer(
            results=[
                InlineQueryResultArticle(
                    id=f"sections:{page}",
                    title="Разделы",
                    input_message_content={
                        "message_text": text,
                        "parse_mode": "HTML",
                        "reply_markup": keyboard.to_dict(),
                    },
                )
            ],
            cache_time=1,
            is_personal=True,
        )
        return

    if req["type"] == "streams":
        section_id = req["section_id"]
        page = req["page"]

        streams = get_online_streams(section_id)
        streams.sort(key=lambda x: x.get("viewers", 0), reverse=True)

        page_size = 5
        start = page * page_size
        items = streams[start : start + page_size]

        text = "<b>Онлайн-стримы</b>\n\n" + format_streams_for_text(items)
        keyboard = build_streams_keyboard(section_id=section_id, page=page)

        await iq.answer(
            results=[
                InlineQueryResultArticle(
                    id=f"streams:{section_id}:{page}",
                    title="Стримы",
                    input_message_content={
                        "message_text": text,
                        "parse_mode": "HTML",
                        "reply_markup": keyboard.to_dict(),
                    },
                )
            ],
            cache_time=1,
            is_personal=True,
        )
        return


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("Handling /start command...")
    query = f"{MENU_PREFIX}:sections:0"
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📋 Открыть меню",
                    switch_inline_query_current_chat=query,
                )
            ]
        ]
    )

    await update.message.reply_text(
        "Меню формируется динамически через inlinequery.",
        reply_markup=keyboard,
    )


def setup_app():
    print("Setting up the Telegram bot application...")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(InlineQueryHandler(inline_menu_handler))
    return app

