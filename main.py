import os
import requests

from flask import Flask, request, redirect
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

REDIRECT_URI = "http://127.0.0.1:3000/callback"

SCOPE = "user-read-private user-top-read"

access_token = None
refresh_token = None


@app.route("/")
def login():

    url = "https://accounts.spotify.com/authorize"

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE
    }

    response = requests.Request(
        "GET",
        url,
        params=params
    ).prepare()

    return redirect(response.url)


@app.route("/callback")
def callback():

    code = request.args.get("code")

    if not code:
        return "Authorization code not received."

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI
        },
        auth=(CLIENT_ID, CLIENT_SECRET)
    )

    token_data = response.json()

    access_token = token_data["access_token"]

    spotify_response = requests.get(
        "https://api.spotify.com/v1/me",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    return spotify_response.json()


app.run(
    host="127.0.0.1",
    port=3000
)