"""Encode url"""
from urllib.parse import urlencode
import re
import os
import requests
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)
from flask import request, redirect, abort, url_for, render_template
from sqlalchemy import (
    text,
)
from app import engine, app, db
from app.models import User, Votes, Games, VotesSchema
from app.functions import validate, get_user_info
from app.decorators import admin_required


steam_id_re = re.compile("https://steamcommunity.com/openid/id/(.*?)$")
steam_openid_url = "https://steamcommunity.com/openid/login"

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/auth")
def auth_with_steam():
    """Authenticate an user via Steam

    Returns:
        redirect: Redirect to the Steam login page
    """
    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.mode": "checkid_setup",
        "openid.return_to": os.environ["URL"] + "/authorize",
        "openid.realm": os.environ["URL"],
    }

    query_string = urlencode(params)
    auth_url = steam_openid_url + "?" + query_string

    return redirect(auth_url)


@app.route("/authorize")
def authorize():
    """Verify the Steam user and login

    Returns:
        redirect: Redirect to sucess page or 401
    """
    valid = validate(request.args, steam_openid_url)
    if valid is False:
        return abort(401)
    match = steam_id_re.search(dict(request.args)["openid.identity"])
    db_user = User.get_or_create(match.group(1))
    steam_data = get_user_info(db_user.steam_id)
    db_user.nickname = steam_data["personaname"]
    db.session.commit()
    login_user(user=db_user, remember=True)
    return redirect(url_for("login_success"))


@app.route("/success")
@login_required
def login_success():
    """Status page if login is successful

    Returns:
        String: Logged in info message
    """
    return (
        "You are logged in as "
        + current_user.nickname
        + ". Refresh the Steam page to start voting!"
    )


@app.route("/user")
@login_required
def user():
    """Get user info and check if authenticated

    Returns:
        Object: is_authenticated and optional the name
    """

    if current_user.is_authenticated:
        return {"is_authenticated": True, "name": current_user.nickname}
    return {"is_authenticated": False}


@app.route("/vote", methods=["POST"])
@login_required
def vote():
    """User can vote

    Returns:
        Object: Return votes summary
    """
    data = request.get_json()
    user_vote = False
    if current_user.is_authenticated:
        data["user_id"] = current_user.id
        Votes.update_or_create(data)

        # Copied from votes
        mapping = {1: "kb", 2: "controller"}
        sql = text(
            "SELECT vote, count(vote) from votes where app_id ="
            + data["app_id"]
            + " and deleted = False "
            + "group by vote"
        )
        results = engine.execute(sql)
        voters = {mapping[1]: 0, mapping[2]: 0}
        total = 0
        for key, value in results:
            voters[mapping[key]] = value
            total = total + value

        user_vote = (
            Votes.query.filter_by(user_id=current_user.id)
            .filter_by(app_id=data["app_id"])
            .filter_by(deleted=False)
            .first()
        )
        if user_vote:
            vote_schema = VotesSchema()
            user_vote = vote_schema.dump(user_vote)
            user_vote = mapping[user_vote["vote"]]

        return {
            "result": voters,
            "total": total,
            "user_vote": user_vote,
            "is_authenticated": current_user.is_authenticated,
        }
    return {"success": False}


@app.route("/votes/<steam_id>")
def votes(steam_id):
    """Votes of a specific game

    Args:
        steam_id (Integer): Steam game id

    Returns:
        Object: Return votes summary
    """

    mapping = {1: "kb", 2: "controller"}
    game = Games.query.get(steam_id)
    if game is None:
        return {"error": "This game in not indexed or available to vote"}

    sql = text(
        "SELECT vote, count(vote) from votes where app_id ="
        + steam_id
        + " AND deleted = False "
        + "group by vote"
    )
    results = engine.execute(sql)
    voters = {mapping[1]: 0, mapping[2]: 0}
    total = 0
    for key, value in results:
        voters[mapping[key]] = value
        total = total + value
    user_vote = False
    if current_user.is_authenticated:
        user_vote = (
            Votes.query.filter_by(user_id=current_user.id)
            .filter_by(app_id=steam_id)
            .filter_by(deleted=False)
            .first()
        )
        vote_schema = VotesSchema()
        user_vote = vote_schema.dump(user_vote)
        if user_vote:
            user_vote = mapping[user_vote["vote"]]

    return {
        "result": voters,
        "total": total,
        "user_vote": user_vote,
        "is_authenticated": current_user.is_authenticated,
    }


@app.route("/logout")
@login_required
def logout():
    """Logout the current user

    Returns:
        Object: Status of user
    """
    logout_user()
    if current_user.is_authenticated:
        return {"success": False}
    return {"success": True}


@app.route("/update-games")
@admin_required
def update_games():
    """Update or create Steam games in DB

    Returns:
        String: done message
    """

    url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/?format=json"
    steam_request = requests.get(url=url, params={})
    data = steam_request.json()
    for steam_game in reversed(data["applist"]["apps"]):
        Games.update_or_create(steam_game)

    return "Games updated"
