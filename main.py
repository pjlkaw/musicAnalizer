import os
import requests
import pandas as pd

from flask import Flask, request, redirect, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

app = Flask(__name__)

CORS(app)


CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

REDIRECT_URI = "http://127.0.0.1:3000/callback"

SCOPE = (
    "user-read-private "
    "user-top-read "
    "playlist-read-private "
    "user-library-read"
)


# ============================================================
# AUTHENTICATION
# ============================================================

access_token = None
refresh_token = None


# ============================================================
# FRONTEND
# ============================================================

@app.route("/app")
def app_page():
    return send_from_directory(".", "index.html")


@app.route("/frontend/<path:filename>")
def frontend(filename):
    return send_from_directory("frontend", filename)


# ============================================================
# LOGIN
# ============================================================

@app.route("/")
def login():

    spotify_url = "https://accounts.spotify.com/authorize"

    parameters = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE
    }

    prepared_request = requests.Request(
        "GET",
        spotify_url,
        params=parameters
    ).prepare()

    return redirect(prepared_request.url)


# ============================================================
# CALLBACK
# ============================================================

@app.route("/callback")
def callback():

    global access_token
    global refresh_token

    authorization_code = request.args.get("code")

    if not authorization_code:
        return "Authorization code not received.", 400

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": REDIRECT_URI
        },
        auth=(CLIENT_ID, CLIENT_SECRET),
        timeout=10
    )

    if response.status_code != 200:
        return response.json(), response.status_code

    token_data = response.json()

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    return redirect("/app")


# ============================================================
# SPOTIFY API
# ============================================================

def spotify_get(endpoint):
    """
    Send a GET request to the Spotify Web API.

    Returns:
        A dictionary containing the API response.
        Returns an empty dictionary when the request fails.
    """

    if not access_token:
        return {}

    response = requests.get(
        endpoint,
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        timeout=10
    )

    if response.status_code != 200:
        return {}

    return response.json()


# ============================================================
# DATAFRAME CREATION
# ============================================================

def create_artists_dataframe(artists_data):
    """
    Convert Spotify artist data into a Pandas DataFrame.
    """

    artists = []

    for artist in artists_data.get("items", []):

        artists.append({
            "id": artist.get("id"),
            "name": artist.get("name"),
            "popularity": artist.get("popularity", 0),
            "followers": artist.get("followers", {}).get("total", 0),
            "genres": artist.get("genres", [])
        })

    return pd.DataFrame(artists)


def create_tracks_dataframe(tracks_data):
    """
    Convert Spotify track data into a Pandas DataFrame.
    """

    tracks = []

    for track in tracks_data.get("items", []):

        artist_names = []

        for artist in track.get("artists", []):
            artist_names.append(
                artist.get("name", "")
            )

        album = track.get("album", {})

        album_images = album.get("images") or []

        image_url = None

        if album_images:
            image_url = album_images[0].get("url")

        tracks.append({
            "id": track.get("id"),
            "name": track.get("name"),
            "artists": ", ".join(artist_names),
            "artist_ids": [
                artist.get("id")
                for artist in track.get("artists", [])
            ],
            "album_id": album.get("id"),
            "album": album.get("name"),
            "album_type": album.get("album_type"),
            "release_date": album.get("release_date"),
            "image": image_url,
            "popularity": track.get("popularity", 0),
            "preview_url": track.get("preview_url")
        })

    return pd.DataFrame(tracks)


def create_playlists_dataframe(playlists_data):
    """
    Convert Spotify playlist data into a Pandas DataFrame.
    """

    playlists = []

    for playlist in playlists_data.get("items", []):

        playlist_images = playlist.get("images") or []

        image_url = None

        if playlist_images:
            image_url = playlist_images[0].get("url")

        playlists.append({
            "id": playlist.get("id"),
            "name": playlist.get("name"),
            "tracks": playlist.get(
                "items",
                {}
            ).get(
                "total",
                playlist.get(
                    "tracks",
                    {}
                ).get("total", 0)
            ),
            "image": image_url,
            "public": playlist.get("public"),
            "description": playlist.get(
                "description"
            )
        })

    return pd.DataFrame(playlists)


def create_saved_albums_dataframe(albums_data):
    """
    Convert saved album data into a Pandas DataFrame.
    """

    albums = []

    for item in albums_data.get("items", []):

        album = item.get("album", {})

        album_images = album.get("images") or []

        image_url = None

        if album_images:
            image_url = album_images[0].get("url")

        artist_names = []

        for artist in album.get("artists", []):
            artist_names.append(
                artist.get("name", "")
            )

        albums.append({
            "id": album.get("id"),
            "name": album.get("name"),
            "artists": ", ".join(artist_names),
            "album_type": album.get("album_type"),
            "total_tracks": album.get(
                "total_tracks",
                0
            ),
            "release_date": album.get(
                "release_date"
            ),
            "image": image_url,
            "added_at": item.get("added_at")
        })

    return pd.DataFrame(albums)


# ============================================================
# DATA CLEANING
# ============================================================

def clean_numeric_columns(dataframe, columns):
    """
    Convert selected DataFrame columns into numeric values.
    Invalid values become zero.
    """

    for column in columns:

        if column in dataframe.columns:

            dataframe[column] = pd.to_numeric(
                dataframe[column],
                errors="coerce"
            ).fillna(0)

    return dataframe


# ============================================================
# ARTIST ANALYSIS
# ============================================================

def analyze_artists(artists_df):

    if artists_df.empty:
        return {
            "total": 0,
            "average_popularity": 0,
            "highest_popularity": 0,
            "average_followers": 0,
            "total_followers": 0,
            "artists": []
        }

    artists_df = artists_df.copy()

    artists_df = clean_numeric_columns(
        artists_df,
        [
            "popularity",
            "followers"
        ]
    )

    artists_df = artists_df.sort_values(
        by="popularity",
        ascending=False
    )

    return {
        "total": int(len(artists_df)),

        "average_popularity": round(
            artists_df["popularity"].mean(),
            2
        ),

        "highest_popularity": int(
            artists_df["popularity"].max()
        ),

        "average_followers": int(
            artists_df["followers"].mean()
        ),

        "total_followers": int(
            artists_df["followers"].sum()
        ),

        "artists": artists_df.drop(
            columns=["genres"],
            errors="ignore"
        ).to_dict(
            orient="records"
        )
    }


# ============================================================
# TRACK ANALYSIS
# ============================================================

def analyze_tracks(tracks_df):

    if tracks_df.empty:
        return {
            "total": 0,
            "unique_artists": 0,
            "unique_albums": 0,
            "average_popularity": 0,
            "highest_popularity": 0,
            "tracks": []
        }

    tracks_df = tracks_df.copy()

    tracks_df = clean_numeric_columns(
        tracks_df,
        ["popularity"]
    )

    tracks_df = tracks_df.sort_values(
        by="popularity",
        ascending=False
    )

    unique_artists = set()

    for artist_ids in tracks_df["artist_ids"]:

        for artist_id in artist_ids:
            if artist_id:
                unique_artists.add(artist_id)

    unique_albums = (
        tracks_df["album_id"]
        .dropna()
        .nunique()
    )

    return {
        "total": int(len(tracks_df)),

        "unique_artists": int(
            len(unique_artists)
        ),

        "unique_albums": int(
            unique_albums
        ),

        "average_popularity": round(
            tracks_df["popularity"].mean(),
            2
        ),

        "highest_popularity": int(
            tracks_df["popularity"].max()
        ),

        "tracks": tracks_df.drop(
            columns=["artist_ids"],
            errors="ignore"
        ).to_dict(
            orient="records"
        )
    }


# ============================================================
# ALBUM ANALYSIS
# ============================================================

def create_albums_from_tracks(tracks_df):

    if tracks_df.empty:
        return pd.DataFrame()

    album_columns = [
        "album_id",
        "album",
        "artists",
        "album_type",
        "release_date",
        "image"
    ]

    available_columns = []

    for column in album_columns:

        if column in tracks_df.columns:
            available_columns.append(column)

    albums_df = tracks_df[
        available_columns
    ].copy()

    albums_df = albums_df.drop_duplicates(
        subset=["album_id"]
    )

    return albums_df


def analyze_albums(tracks_df):

    if tracks_df.empty:
        return {
            "total": 0,
            "albums": []
        }

    albums_df = create_albums_from_tracks(
        tracks_df
    )

    return {
        "total": int(len(albums_df)),

        "albums": albums_df.to_dict(
            orient="records"
        )
    }


# ============================================================
# GENRE ANALYSIS
# ============================================================

def analyze_genres(artists_df):

    if artists_df.empty:
        return []

    if "genres" not in artists_df.columns:
        return []

    genres = artists_df["genres"].explode()

    genres = genres.dropna()

    genres = genres[
        genres != ""
    ]

    genre_counts = genres.value_counts()

    genre_dataframe = (
        genre_counts
        .head(15)
        .reset_index()
    )

    genre_dataframe.columns = [
        "name",
        "count"
    ]

    return genre_dataframe.to_dict(
        orient="records"
    )


# ============================================================
# PLAYLIST ANALYSIS
# ============================================================

def analyze_playlists(playlists_df):

    if playlists_df.empty:
        return {
            "total": 0,
            "total_tracks": 0,
            "average_tracks": 0,
            "largest_playlist": None,
            "playlists": []
        }

    playlists_df = playlists_df.copy()

    playlists_df = clean_numeric_columns(
        playlists_df,
        ["tracks"]
    )

    playlists_df = playlists_df.sort_values(
        by="tracks",
        ascending=False
    )

    largest_playlist = None

    if not playlists_df.empty:

        largest_playlist = (
            playlists_df.iloc[0]
            .to_dict()
        )

    return {
        "total": int(len(playlists_df)),

        "total_tracks": int(
            playlists_df["tracks"].sum()
        ),

        "average_tracks": round(
            playlists_df["tracks"].mean(),
            2
        ),

        "largest_playlist": largest_playlist,

        "playlists": playlists_df.to_dict(
            orient="records"
        )
    }


# ============================================================
# PERIOD COMPARISON
# ============================================================

def compare_periods(period_data):

    comparison = {}

    for period_name, dataframe in period_data.items():

        if dataframe.empty:
            comparison[period_name] = {
                "total": 0,
                "average_popularity": 0
            }

            continue

        dataframe = dataframe.copy()

        dataframe = clean_numeric_columns(
            dataframe,
            ["popularity"]
        )

        comparison[period_name] = {
            "total": int(len(dataframe)),

            "average_popularity": round(
                dataframe["popularity"].mean(),
                2
            ),

            "highest_popularity": int(
                dataframe["popularity"].max()
            )
        }

    return comparison


# ============================================================
# REPEATED ITEMS
# ============================================================

def find_repeated_items(period_data, column):

    appearances = {}

    for period_name, dataframe in period_data.items():

        if dataframe.empty:
            continue

        if column not in dataframe.columns:
            continue

        for item_id in dataframe[column].dropna():

            if item_id not in appearances:
                appearances[item_id] = []

            appearances[item_id].append(
                period_name
            )

    repeated = []

    for item_id, periods in appearances.items():

        if len(periods) >= 2:

            repeated.append({
                "id": item_id,
                "periods": periods,
                "period_count": len(periods)
            })

    return repeated


# ============================================================
# CROSS-PERIOD ANALYSIS
# ============================================================

def analyze_cross_period_data(
    artists_by_period,
    tracks_by_period
):

    repeated_artists = find_repeated_items(
        artists_by_period,
        "id"
    )

    repeated_tracks = find_repeated_items(
        tracks_by_period,
        "id"
    )

    return {
        "repeated_artists": repeated_artists,

        "repeated_tracks": repeated_tracks,

        "artist_stability": {
            "artists_in_multiple_periods": len(
                repeated_artists
            )
        },

        "track_stability": {
            "tracks_in_multiple_periods": len(
                repeated_tracks
            )
        }
    }


# ============================================================
# GLOBAL ANALYSIS
# ============================================================

def analyze_global_data(
    artists_by_period,
    tracks_by_period
):

    all_artists = []

    for dataframe in artists_by_period.values():

        if not dataframe.empty:
            all_artists.append(dataframe)

    all_tracks = []

    for dataframe in tracks_by_period.values():

        if not dataframe.empty:
            all_tracks.append(dataframe)

    if all_artists:

        combined_artists = pd.concat(
            all_artists,
            ignore_index=True
        )

        unique_artists = (
            combined_artists
            .drop_duplicates(
                subset=["id"]
            )
        )

    else:
        unique_artists = pd.DataFrame()


    if all_tracks:

        combined_tracks = pd.concat(
            all_tracks,
            ignore_index=True
        )

        unique_tracks = (
            combined_tracks
            .drop_duplicates(
                subset=["id"]
            )
        )

    else:
        unique_tracks = pd.DataFrame()


    return {
        "unique_artists": int(
            len(unique_artists)
        ),

        "unique_tracks": int(
            len(unique_tracks)
        )
    }


# ============================================================
# MAIN STATISTICS ENDPOINT
# ============================================================

@app.route("/stats")
def stats():

    if not access_token:
        return "Not authenticated.", 401


    # --------------------------------------------------------
    # Get user profile
    # --------------------------------------------------------

    profile_data = spotify_get(
        "https://api.spotify.com/v1/me"
    )


    # --------------------------------------------------------
    # Get top artists and tracks
    # --------------------------------------------------------

    periods = [
        "short_term",
        "medium_term",
        "long_term"
    ]

    artists_by_period = {}
    tracks_by_period = {}


    for period in periods:

        artists_response = spotify_get(
            "https://api.spotify.com/v1/me/top/artists"
            f"?limit=50&time_range={period}"
        )

        tracks_response = spotify_get(
            "https://api.spotify.com/v1/me/top/tracks"
            f"?limit=50&time_range={period}"
        )

        artists_by_period[period] = (
            create_artists_dataframe(
                artists_response
            )
        )

        tracks_by_period[period] = (
            create_tracks_dataframe(
                tracks_response
            )
        )


    # --------------------------------------------------------
    # Get playlists
    # --------------------------------------------------------

    playlists_data = spotify_get(
        "https://api.spotify.com/v1/me/playlists?limit=50"
    )

    playlists_df = create_playlists_dataframe(
        playlists_data
    )


    # --------------------------------------------------------
    # Get saved tracks
    # --------------------------------------------------------

    saved_tracks_data = spotify_get(
        "https://api.spotify.com/v1/me/tracks?limit=1"
    )


    # --------------------------------------------------------
    # Get saved albums
    # --------------------------------------------------------

    saved_albums_data = spotify_get(
        "https://api.spotify.com/v1/me/albums?limit=50"
    )

    saved_albums_df = create_saved_albums_dataframe(
        saved_albums_data
    )


    # ========================================================
    # ANALYZE EACH PERIOD
    # ========================================================

    artists_analysis = {}
    tracks_analysis = {}
    albums_analysis = {}
    genres_analysis = {}


    for period in periods:

        artists_df = artists_by_period[period]

        tracks_df = tracks_by_period[period]


        artists_analysis[period] = (
            analyze_artists(
                artists_df
            )
        )


        tracks_analysis[period] = (
            analyze_tracks(
                tracks_df
            )
        )


        albums_analysis[period] = (
            analyze_albums(
                tracks_df
            )
        )


        genres_analysis[period] = (
            analyze_genres(
                artists_df
            )
        )


    # ========================================================
    # COMPARISONS
    # ========================================================

    artist_comparison = compare_periods(
        artists_by_period
    )

    track_comparison = compare_periods(
        tracks_by_period
    )


    cross_period_analysis = (
        analyze_cross_period_data(
            artists_by_period,
            tracks_by_period
        )
    )


    global_analysis = analyze_global_data(
        artists_by_period,
        tracks_by_period
    )


    # ========================================================
    # SAVED ALBUM ANALYSIS
    # ========================================================

    saved_albums = {
        "total": int(
            saved_albums_data.get(
                "total",
                len(saved_albums_df)
            )
        ),

        "loaded": int(
            len(saved_albums_df)
        ),

        "albums": saved_albums_df.to_dict(
            orient="records"
        )
    }


    # ========================================================
    # PLAYLIST ANALYSIS
    # ========================================================

    playlist_analysis = analyze_playlists(
        playlists_df
    )


    # ========================================================
    # SUMMARY
    # ========================================================

    short_artists = artists_by_period[
        "short_term"
    ]

    short_tracks = tracks_by_period[
        "short_term"
    ]

    long_artists = artists_by_period[
        "long_term"
    ]

    long_tracks = tracks_by_period[
        "long_term"
    ]


    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {

        "profile": {
            "id": profile_data.get("id"),
            "name": profile_data.get(
                "display_name"
            ),
            "image": (
                profile_data.get("images") or [{}]
            )[0].get("url")
        },


        "summary": {

            "top_artists_short_term": int(
                len(short_artists)
            ),

            "top_tracks_short_term": int(
                len(short_tracks)
            ),

            "top_artists_long_term": int(
                len(long_artists)
            ),

            "top_tracks_long_term": int(
                len(long_tracks)
            ),

            "playlists": int(
                playlists_data.get(
                    "total",
                    len(playlists_df)
                )
            ),

            "saved_tracks": int(
                saved_tracks_data.get(
                    "total",
                    0
                )
            ),

            "saved_albums": int(
                saved_albums_data.get(
                    "total",
                    len(saved_albums_df)
                )
            ),

            "unique_artists": global_analysis[
                "unique_artists"
            ],

            "unique_tracks": global_analysis[
                "unique_tracks"
            ]
        },


        "artists": {

            "short_term":
                artists_analysis[
                    "short_term"
                ],

            "medium_term":
                artists_analysis[
                    "medium_term"
                ],

            "long_term":
                artists_analysis[
                    "long_term"
                ]
        },


        "tracks": {

            "short_term":
                tracks_analysis[
                    "short_term"
                ],

            "medium_term":
                tracks_analysis[
                    "medium_term"
                ],

            "long_term":
                tracks_analysis[
                    "long_term"
                ]
        },


        "albums": {

            "short_term":
                albums_analysis[
                    "short_term"
                ],

            "medium_term":
                albums_analysis[
                    "medium_term"
                ],

            "long_term":
                albums_analysis[
                    "long_term"
                ],

            "saved":
                saved_albums
        },


        "genres": {

            "short_term":
                genres_analysis[
                    "short_term"
                ],

            "medium_term":
                genres_analysis[
                    "medium_term"
                ],

            "long_term":
                genres_analysis[
                    "long_term"
                ]
        },


        "playlists": playlist_analysis,


        "comparison": {

            "artists":
                artist_comparison,

            "tracks":
                track_comparison
        },


        "cross_period": cross_period_analysis,


        "analysis": {

            "artists": {

                "short_term_average_popularity":
                    artists_analysis[
                        "short_term"
                    ][
                        "average_popularity"
                    ],

                "medium_term_average_popularity":
                    artists_analysis[
                        "medium_term"
                    ][
                        "average_popularity"
                    ],

                "long_term_average_popularity":
                    artists_analysis[
                        "long_term"
                    ][
                        "average_popularity"
                    ]
            },

            "tracks": {

                "short_term_average_popularity":
                    tracks_analysis[
                        "short_term"
                    ][
                        "average_popularity"
                    ],

                "medium_term_average_popularity":
                    tracks_analysis[
                        "medium_term"
                    ][
                        "average_popularity"
                    ],

                "long_term_average_popularity":
                    tracks_analysis[
                        "long_term"
                    ][
                        "average_popularity"
                    ]
            },

            "playlists": {

                "total":
                    playlist_analysis[
                        "total"
                    ],

                "total_tracks":
                    playlist_analysis[
                        "total_tracks"
                    ],

                "average_tracks":
                    playlist_analysis[
                        "average_tracks"
                    ],

                "largest_playlist":
                    playlist_analysis[
                        "largest_playlist"
                    ]
            },

            "library": {

                "saved_tracks":
                    saved_tracks_data.get(
                        "total",
                        0
                    ),

                "saved_albums":
                    saved_albums_data.get(
                        "total",
                        len(saved_albums_df)
                    )
            }
        }
    }


# ============================================================
# START SERVER
# ============================================================

app.run(
    host="127.0.0.1",
    port=3000
)