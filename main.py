import os
import requests
import pandas as pd
from dotenv import load_dotenv
from flask import Flask, redirect, request, render_template

load_dotenv()

app = Flask(__name__)

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

REDIRECT_URI = "http://127.0.0.1:3000/callback"

SPOTIFY_API = "https://api.spotify.com/v1"
SPOTIFY_ACCOUNTS = "https://accounts.spotify.com"

SCOPE = "user-read-private user-top-read user-library-read playlist-read-private user-read-recently-played"

access_token = None
refresh_token = None

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ============================================================
# HELPERS
# ============================================================

def spotify_get(path, params=None):
    if not access_token:
        return None, 401

    response = requests.get(
        f"{SPOTIFY_API}{path}",
        headers={"Authorization": f"Bearer {access_token}"},
        params=params,
        timeout=10
    )

    try:
        data = response.json()
    except ValueError:
        data = {"error": response.text}

    return data, response.status_code


def dataframe_to_json(df):
    # Converte NaN/NaT do Pandas para None antes do JSON.
    df = df.astype(object).where(pd.notna(df), None)
    return df.to_dict(orient="records")


def first_image(images):
    if not images:
        return None
    return images[0].get("url")


def artist_names(artists):
    return ", ".join(
        artist.get("name", "")
        for artist in artists or []
    )


# ============================================================
# LOGIN
# ============================================================

@app.route("/")
def login():
    url = f"{SPOTIFY_ACCOUNTS}/authorize"

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
    global access_token, refresh_token

    code = request.args.get("code")

    if not code:
        error = request.args.get("error")

        if error:
            return f"Spotify authorization failed: {error}", 400

        return "Authorization code not received.", 400

    response = requests.post(
        f"{SPOTIFY_ACCOUNTS}/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI
        },
        auth=(CLIENT_ID, CLIENT_SECRET),
        timeout=10
    )

    token_data = response.json()

    if response.status_code != 200:
        return token_data, response.status_code

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    return redirect("/dashboard")


# ============================================================
# PROFILE
# ============================================================

@app.route("/me")
def me():
    data, status = spotify_get("/me")

    if status != 200:
        return data, status

    return {
        "account_id": data.get("account_id"),
        "id": data.get("id"),
        "name": data.get("display_name"),
        "image": first_image(data.get("images")),
        "spotify_url": (data.get("external_urls") or {}).get("spotify")
    }


# ============================================================
# TOP ARTISTS
# ============================================================

@app.route("/top/artists")
def top_artists():
    time_range = request.args.get(
        "time_range",
        "medium_term"
    )

    if time_range not in {
        "short_term",
        "medium_term",
        "long_term"
    }:
        return {
            "error": "Invalid time_range."
        }, 400

    data, status = spotify_get(
        "/me/top/artists",
        params={
            "limit": 50,
            "time_range": time_range
        }
    )

    if status != 200:
        return data, status

    rows = []

    for position, artist in enumerate(
        data.get("items", []),
        start=1
    ):
        rows.append({
            "position": position,
            "id": artist.get("id"),
            "name": artist.get("name"),
            "genres": artist.get("genres") or [],
            "image": first_image(artist.get("images")),
            "spotify_url": (artist.get("external_urls") or {}).get("spotify")
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return {
            "time_range": time_range,
            "total": 0,
            "artists": []
        }

    genre_counts = (
        df["genres"]
        .explode()
        .dropna()
        .value_counts()
        .reset_index()
    )

    genre_counts.columns = ["genre", "count"]

    return {
        "time_range": time_range,
        "total": len(df),
        "genres": dataframe_to_json(genre_counts),
        "artists": dataframe_to_json(df)
    }


# ============================================================
# TOP TRACKS
# ============================================================

@app.route("/top/tracks")
def top_tracks():
    time_range = request.args.get(
        "time_range",
        "medium_term"
    )

    if time_range not in {
        "short_term",
        "medium_term",
        "long_term"
    }:
        return {
            "error": "Invalid time_range."
        }, 400

    data, status = spotify_get(
        "/me/top/tracks",
        params={
            "limit": 50,
            "time_range": time_range
        }
    )

    if status != 200:
        return data, status

    rows = []

    for position, track in enumerate(
        data.get("items", []),
        start=1
    ):
        artists = track.get("artists") or []
        album = track.get("album") or {}

        rows.append({
            "position": position,
            "id": track.get("id"),
            "name": track.get("name"),
            "artists": artist_names(artists),
            "artist_ids": [
                artist.get("id")
                for artist in artists
                if artist.get("id")
            ],
            "album": album.get("name"),
            "album_id": album.get("id"),
            "image": first_image(album.get("images")),
            "duration_ms": track.get("duration_ms"),
            "explicit": track.get("explicit"),
            "spotify_url": (track.get("external_urls") or {}).get("spotify")
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return {
            "time_range": time_range,
            "total": 0,
            "unique_artists": 0,
            "unique_albums": 0,
            "tracks": []
        }

    unique_artists = {
        artist_id
        for artist_ids in df["artist_ids"]
        for artist_id in artist_ids
        if artist_id
    }

    return {
        "time_range": time_range,
        "total": len(df),
        "unique_artists": len(unique_artists),
        "unique_albums": int(df["album_id"].nunique()),
        "tracks": dataframe_to_json(
            df.drop(columns=["artist_ids"])
        )
    }


# ============================================================
# SAVED TRACKS
# ============================================================

@app.route("/saved/tracks")
def saved_tracks():
    data, status = spotify_get(
        "/me/tracks",
        params={
            "limit": 50
        }
    )

    if status != 200:
        return data, status

    rows = []

    for item in data.get("items", []):
        track = item.get("track") or {}
        album = track.get("album") or {}
        artists = track.get("artists") or []

        rows.append({
            "id": track.get("id"),
            "name": track.get("name"),
            "artists": artist_names(artists),
            "artist_ids": [
                artist.get("id")
                for artist in artists
                if artist.get("id")
            ],
            "album": album.get("name"),
            "album_id": album.get("id"),
            "added_at": item.get("added_at"),
            "image": first_image(album.get("images")),
            "duration_ms": track.get("duration_ms"),
            "explicit": track.get("explicit"),
            "spotify_url": (track.get("external_urls") or {}).get("spotify")
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return {
            "total": data.get("total", 0),
            "unique_artists": 0,
            "unique_albums": 0,
            "tracks": []
        }

    unique_artists = {
        artist_id
        for artist_ids in df["artist_ids"]
        for artist_id in artist_ids
        if artist_id
    }

    return {
        "total": data.get("total", 0),
        "loaded": len(df),
        "unique_artists": len(unique_artists),
        "unique_albums": int(df["album_id"].nunique()),
        "tracks": dataframe_to_json(
            df.drop(columns=["artist_ids"])
        )
    }


# ============================================================
# SAVED ALBUMS
# ============================================================

@app.route("/saved/albums")
def saved_albums():
    data, status = spotify_get(
        "/me/albums",
        params={
            "limit": 50
        }
    )

    if status != 200:
        return data, status

    rows = []

    for item in data.get("items", []):
        album = item.get("album") or {}
        artists = album.get("artists") or []

        rows.append({
            "id": album.get("id"),
            "name": album.get("name"),
            "artists": artist_names(artists),
            "artist_ids": [
                artist.get("id")
                for artist in artists
                if artist.get("id")
            ],
            "release_date": album.get("release_date"),
            "release_date_precision": album.get("release_date_precision"),
            "album_type": album.get("album_type"),
            "total_tracks": album.get("total_tracks"),
            "added_at": item.get("added_at"),
            "image": first_image(album.get("images")),
            "spotify_url": (album.get("external_urls") or {}).get("spotify")
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return {
            "total": data.get("total", 0),
            "albums": []
        }

    return {
        "total": data.get("total", 0),
        "loaded": len(df),
        "unique_artists": int(
            df["artist_ids"]
            .explode()
            .dropna()
            .nunique()
        ),
        "albums": dataframe_to_json(
            df.drop(columns=["artist_ids"])
        )
    }


# ============================================================
# PLAYLISTS
# ============================================================

@app.route("/playlists")
def playlists():
    data, status = spotify_get(
        "/me/playlists",
        params={
            "limit": 50
        }
    )

    if status != 200:
        return data, status

    rows = []

    for playlist in data.get("items", []):
        if not playlist:
            continue

        items = playlist.get("items") or {}

        rows.append({
            "id": playlist.get("id"),
            "name": playlist.get("name"),
            "items": items.get("total"),
            "public": playlist.get("public"),
            "collaborative": playlist.get("collaborative"),
            "description": playlist.get("description") or "",
            "image": first_image(playlist.get("images")),
            "spotify_url": (playlist.get("external_urls") or {}).get("spotify")
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return {
            "total": data.get("total", 0),
            "loaded": 0,
            "total_items": 0,
            "average_items": 0,
            "playlists": []
        }

    df["items"] = pd.to_numeric(
        df["items"],
        errors="coerce"
    ).fillna(0)

    return {
        "total": data.get("total", 0),
        "loaded": len(df),
        "total_items": int(df["items"].sum()),
        "average_items": round(df["items"].mean(), 2),
        "playlists": dataframe_to_json(
            df.sort_values(
                "items",
                ascending=False
            )
        )
    }


# ============================================================
# RECENTLY PLAYED
# ============================================================

@app.route("/recently-played")
def recently_played():
    data, status = spotify_get(
        "/me/player/recently-played",
        params={
            "limit": 50
        }
    )

    if status != 200:
        return data, status

    rows = []

    for item in data.get("items", []):
        track = item.get("track") or {}
        album = track.get("album") or {}
        artists = track.get("artists") or {}
        context = item.get("context") or {}

        rows.append({
            "played_at": item.get("played_at"),
            "id": track.get("id"),
            "name": track.get("name"),
            "artists": artist_names(artists),
            "artist_ids": [
                artist.get("id")
                for artist in artists
                if artist.get("id")
            ],
            "album": album.get("name"),
            "album_id": album.get("id"),
            "image": first_image(album.get("images")),
            "context_type": context.get("type"),
            "context_uri": context.get("uri"),
            "spotify_url": (track.get("external_urls") or {}).get("spotify")
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return {
            "total": 0,
            "unique_tracks": 0,
            "unique_artists": 0,
            "history": []
        }

    unique_artists = {
        artist_id
        for artist_ids in df["artist_ids"]
        for artist_id in artist_ids
        if artist_id
    }

    return {
        "total": len(df),
        "unique_tracks": int(df["id"].nunique()),
        "unique_artists": len(unique_artists),
        "history": dataframe_to_json(
            df.drop(columns=["artist_ids"])
        )
    }


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=3000,
        debug=True
    )
