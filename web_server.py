from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from genius import search_song
from lrclib_api import get_lyrics

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory="webapp"),
    name="static"
)

@app.get("/")
async def root():
    return FileResponse("webapp/index.html")

@app.get("/api/search")
async def api_search(q: str):

    songs = await search_song(q)

    return songs


@app.get("/api/song")
async def api_song(
    artist: str,
    title: str
):

    lyrics = await get_lyrics(
        artist,
        title
    )

    return {
        "lyrics": lyrics
    }
