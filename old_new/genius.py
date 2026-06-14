
import os,aiohttp
TOKEN=os.getenv("GENIUS_TOKEN")
async def search_song(query):
    async with aiohttp.ClientSession() as s:
        async with s.get("https://api.genius.com/search",
            headers={"Authorization":f"Bearer {TOKEN}"},
            params={"q":query}) as r:
            if r.status!=200: return []
            data=await r.json()
    out=[]
    for hit in data["response"]["hits"]:
        x=hit["result"]
        out.append({
            "artist":x["primary_artist"]["name"],
            "title":x["title"],
            "views":x.get("stats",{}).get("pageviews",0)
        })
    out.sort(key=lambda x:x["views"], reverse=True)
    return out
