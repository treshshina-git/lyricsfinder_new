import aiohttp
import re


def normalize(text):
    text = re.sub(r"\(.*?\)", "", text)
    return text.strip()


async def get_lyrics(artist, title):

    artist = normalize(artist)
    title = normalize(title)

    query = f"{artist} {title}"

    async with aiohttp.ClientSession() as session:

        async with session.get(
            "https://lrclib.net/api/search",
            params={"q": query}
        ) as response:

            if response.status != 200:
                return None

            results = await response.json()

        if not results:
            return None

        # ищем наиболее похожее совпадение
        for song in results:

            if title.lower() in song.get(
                "trackName", ""
            ).lower():

                return (
                    song.get("plainLyrics")
                    or song.get("syncedLyrics")
                )

        first = results[0]

        return (
            first.get("plainLyrics")
            or first.get("syncedLyrics")
        )
