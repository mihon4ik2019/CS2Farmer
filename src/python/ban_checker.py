import requests
import time
from typing import Optional

class BanChecker:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.cache = {}

    def check_account(self, steam_id: str) -> Optional[bool]:
        if not steam_id:
            return None
        if steam_id in self.cache:
            banned, ts = self.cache[steam_id]
            if time.time() - ts < 300:
                return banned
        url = f"https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/?key={self.api_key}&steamids={steam_id}"
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            players = data.get('players', [])
            if not players:
                return None
            player = players[0]
            banned = player.get('VACBanned', False) or player.get('NumberOfGameBans', 0) > 0
            self.cache[steam_id] = (banned, time.time())
            return banned
        except Exception:
            return None