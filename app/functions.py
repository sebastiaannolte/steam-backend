import requests
from app import login_manager
from app.models import User
import urllib.request
import os
from flask import json


def validate(signed_params, steam_url):
    """Validate the authentication

    Returns:
        boolean
    """
    params = {
        "openid.assoc_handle": signed_params["openid.assoc_handle"],
        "openid.sig": signed_params["openid.sig"],
        "openid.ns": signed_params["openid.ns"],
        "openid.mode": "check_authentication",
    }
    signed_params = signed_params.to_dict()
    signed_params.update(params)

    signed_params["openid.mode"] = "check_authentication"
    signed_params["openid.signed"] = signed_params["openid.signed"]

    req = requests.post(steam_url, data=signed_params)

    if "is_valid:true" in req.text:
        return True

    return False


@login_manager.user_loader
def load_user(user_id):
    """Load the user for Flask-login

    Args:
        user_id (Integer): The user_id to load

    Returns:
        User: User model
    """
    return User.query.get(user_id)


def get_user_info(steam_id):
    """Get user info from the steam api

    Args:
        steam_id (Integer): Steam ID of the user

    Returns:
        Object: Steam user
    """
    options = {"key": os.environ["STEAM_API_KEY"], "steamids": steam_id}
    url = (
        "https://api.steampowered.com/ISteamUser/"
        "GetPlayerSummaries/v0002/?%s" % urllib.parse.urlencode(options)
    )

    response = json.load(urllib.request.urlopen(url))
    return response["response"]["players"][0] or {}
