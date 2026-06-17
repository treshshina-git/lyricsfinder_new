import time
import base64
import requests
from app.config import VK_CLIENT_ID, VK_CLIENT_SECRET, TOKEN_VK_URL

_cached_token = None
_expire_at = 0
print("Token manager initialized. Ready to fetch access tokens when needed.")
def get_access_token():
    global _cached_token, _expire_at
    now = int(time.time())
    if _cached_token and now < _expire_at - 60:
        return _cached_token

    credentials = f"{VK_CLIENT_ID}:{VK_CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()
    print("Fetching new access token from VK API...")   
    r = requests.post(
        TOKEN_VK_URL,
        headers={
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    _cached_token = data["access_token"]
    _expire_at = now + int(data.get("expire_time", 3600))
    return _cached_token

