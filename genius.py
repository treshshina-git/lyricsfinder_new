import aiohttp
import os
import re

GENIUS_TOKEN = os.getenv("GENIUS_TOKEN")


def normalize(text: str) -> str:
    text = text.lower()

    # удаляем скобки
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"\[.*?\]", "", text)

    # убираем лишние пробелы
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def relevance_score(query: str, artist: str, title: str) -> int:

    query = query.lower()
    artist_l = artist.lower()
    title_l = title.lower()

    score = 0

    # точное совпадение названия
    if query == title_l:
        score += 100

    # запрос входит в название
    if query in title_l:
        score += 50

    # запрос входит в исполнителя
    if query in artist_l:
        score += 20

    # штрафы за менее желательные версии
    bad_words = [
        "remix",
        "live",
        "karaoke",
        "instrumental",
        "acoustic"
    ]

    for word in bad_words:
        if word in title_l:
            score -= 15

    return score


async def search_song(query: str):

    url = "https://api.genius.com/search"

    headers = {
        "Authorization": f"Bearer {GENIUS_TOKEN}"
    }

    raw_results = []

    async with aiohttp.ClientSession() as session:

        for page in range(1, 6):

            async with session.get(
                url,
                headers=headers,
                params={
                    "q": query,
                    "page": page
                }
            ) as response:

                if response.status != 200:
                    break

                data = await response.json()

                hits = data["response"]["hits"]

                if not hits:
                    break

                for hit in hits:

                    song = hit["result"]

                    raw_results.append({
                        "title": song["title"],
                        "artist": song["primary_artist"]["name"],
                        "url": song["url"],
                        "id": song["id"],
                        "score": relevance_score(
                            query,
                            song["primary_artist"]["name"],
                            song["title"]
                        ),
                        "views": song.get("stats", {}).get("pageviews", 0)
                    })

    # Удаление дублей
    unique = {}
    
    for song in raw_results:

        key = (
            normalize(song["artist"]),
            normalize(song["title"])
        )

        if key not in unique:
            unique[key] = song

    results = list(unique.values())

    # Сортировка по релевантности
    results.sort(
        key=lambda song: (
            song["score"],
            song["views"]
        ),
        reverse=True
    )
    print(f"RAW: {len(raw_results)}")
    print(f"UNIQUE: {len(results)}")

    return results
