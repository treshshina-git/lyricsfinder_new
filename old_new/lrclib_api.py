
import aiohttp
async def get_lyrics(artist,title):
    async with aiohttp.ClientSession() as s:
        async with s.get("https://lrclib.net/api/get",
            params={"artist_name":artist,"track_name":title}) as r:
            if r.status!=200: return None
            d=await r.json()
            return d.get("plainLyrics") or d.get("syncedLyrics")
