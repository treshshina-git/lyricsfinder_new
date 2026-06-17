import requests
from app.token_manager import get_access_token
from app.config import API_URL_STREAMS, API_URL_SECTIONS
print("VK API module loaded and ready to fetch data.")

def get_online_streams(section_id=None):
    token = get_access_token()
    if API_URL_STREAMS is None:
        raise RuntimeError("API_URL_STREAMS is not configured")
    r = requests.get(
        API_URL_STREAMS,
        headers={"Authorization": f"Bearer {token}"},
        params={
            "limit": 30,
            "offset": 0,
            "category_id": section_id,
            "all_streams": True,
            "has_vk_video": True,
        },
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    streams = []
    for item in data.get("data", {}).get("channels", []):
        stream = item.get("stream", {})
        owner = item.get("owner", {})
        channel = item.get("channel", {})
        uri = channel.get("url", "")
        urik = "https://live.vkvideo.ru/" + uri
        streams.append(
            {
                "title": stream.get("title", "No title"),
                "viewers": stream.get("counters", {}).get("viewers", 0),
                "owner": owner.get("nick", "unknown"),
                "url": urik,
            }
        )
    return streams

print("Fetching online streams from VK API...") 
def get_online_sections():
    token = get_access_token()
    if API_URL_SECTIONS is None:
        raise RuntimeError("API_URL_SECTIONS is not configured")
    r = requests.get(
        API_URL_SECTIONS,
        headers={"Authorization": f"Bearer {token}"},
        params={
            "limit": 20,
            "offset": 0,
            "category_type": "",
        },
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    dar = data.get("data", {}).get("categories", [])
    sections = []
    for item in dar:
        sections.append(
            {
                "id": item.get("id"),
                "name": item.get("title"),
                "viewers": item.get("counters", {}).get("viewers", 0),
            }
        )
    return sections
print("Online sections fetched successfully.")
