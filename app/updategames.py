import requests
import logging
from app.models import Games

def update_games():
    url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/?format=json"
    steam_request = requests.get(url=url, params={})
    data = steam_request.json()
    for steam_game in reversed(data["applist"]["apps"]):
        Games.update_or_create(steam_game)

    logging.info("Games updated")
