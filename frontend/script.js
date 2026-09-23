// ============================================================
// CONFIGURATION
// ============================================================

let spotifyData = null;

let currentPeriod = "short_term";


// ============================================================
// DOM ELEMENTS
// ============================================================

const loadingElement = document.getElementById("loading");
const errorElement = document.getElementById("error");
const errorMessageElement = document.getElementById("error-message");


// ============================================================
// DATA LOADING
// ============================================================

async function loadSpotifyData() {

    try {

        const response = await fetch("/stats");

        if (!response.ok) {
            throw new Error(
                `Server returned status ${response.status}`
            );
        }

        spotifyData = await response.json();

        loadingElement.classList.add("hidden");

        renderDashboard();

    } catch (error) {

        console.error(error);

        loadingElement.classList.add("hidden");

        errorElement.hidden = false;

        errorMessageElement.textContent =
            "Unable to load Spotify data.";
    }
}


// ============================================================
// DASHBOARD
// ============================================================

function renderDashboard() {

    renderProfile();

    renderSummary();

    renderArtists();

    renderTracks();

    renderGenres();

    renderAlbums();

    renderPlaylists();

    renderComparison();

    renderConsistency();
}


// ============================================================
// PROFILE
// ============================================================

function renderProfile() {

    const profile = spotifyData.profile;

    const profileName = document.getElementById(
        "profile-name"
    );

    const profileImage = document.getElementById(
        "profile-image"
    );


    profileName.textContent =
        profile.name || "Spotify User";


    if (profile.image) {

        profileImage.src = profile.image;

    } else {

        profileImage.style.display = "none";
    }
}


// ============================================================
// SUMMARY
// ============================================================

function renderSummary() {

    const summary = spotifyData.summary;


    document.getElementById(
        "summary-artists"
    ).textContent =
        summary.top_artists_short_term;


    document.getElementById(
        "summary-tracks"
    ).textContent =
        summary.top_tracks_short_term;


    document.getElementById(
        "summary-playlists"
    ).textContent =
        summary.playlists;


    document.getElementById(
        "summary-saved-tracks"
    ).textContent =
        summary.saved_tracks;


    document.getElementById(
        "summary-saved-albums"
    ).textContent =
        summary.saved_albums;


    document.getElementById(
        "summary-unique-artists"
    ).textContent =
        summary.unique_artists;


    document.getElementById(
        "summary-unique-tracks"
    ).textContent =
        summary.unique_tracks;
}


// ============================================================
// ARTISTS
// ============================================================

function renderArtists() {

    const artistsData =
        spotifyData.artists[currentPeriod];

    const artists = artistsData.artists;


    document.getElementById(
        "artists-average-popularity"
    ).textContent =
        artistsData.average_popularity;


    document.getElementById(
        "artists-highest-popularity"
    ).textContent =
        artistsData.highest_popularity;


    document.getElementById(
        "artists-average-followers"
    ).textContent =
        formatNumber(
            artistsData.average_followers
        );


    document.getElementById(
        "artists-total-followers"
    ).textContent =
        formatNumber(
            artistsData.total_followers
        );


    const container =
        document.getElementById("artists-list");


    container.innerHTML = "";


    artists.forEach((artist, index) => {

        const item = document.createElement("article");

        item.className = "ranking-item";


        item.innerHTML = `

            <span class="ranking-position">
                ${index + 1}
            </span>

            <div class="ranking-image"></div>

            <div class="ranking-info">

                <div class="ranking-name">
                    ${escapeHTML(artist.name)}
                </div>

                <div class="ranking-subtitle">
                    ${formatNumber(artist.followers)}
                    followers
                </div>

            </div>

            <span class="ranking-value">
                Popularity ${artist.popularity}
            </span>

        `;


        container.appendChild(item);
    });
}


// ============================================================
// TRACKS
// ============================================================

function renderTracks() {

    const tracksData =
        spotifyData.tracks[currentPeriod];

    const tracks = tracksData.tracks;


    document.getElementById(
        "tracks-average-popularity"
    ).textContent =
        tracksData.average_popularity;


    document.getElementById(
        "tracks-highest-popularity"
    ).textContent =
        tracksData.highest_popularity;


    document.getElementById(
        "tracks-unique-artists"
    ).textContent =
        tracksData.unique_artists;


    document.getElementById(
        "tracks-unique-albums"
    ).textContent =
        tracksData.unique_albums;


    const container =
        document.getElementById("tracks-list");


    container.innerHTML = "";


    tracks.forEach((track, index) => {

        const item = document.createElement("article");

        item.className = "ranking-item";


        item.innerHTML = `

            <span class="ranking-position">
                ${index + 1}
            </span>

            <img
                class="ranking-image"
                src="${track.image || ""}"
                alt=""
            >

            <div class="ranking-info">

                <div class="ranking-name">
                    ${escapeHTML(track.name)}
                </div>

                <div class="ranking-subtitle">
                    ${escapeHTML(track.artists)}
                </div>

            </div>

            <span class="ranking-value">
                Popularity ${track.popularity}
            </span>

        `;


        container.appendChild(item);
    });
}


// ============================================================
// GENRES
// ============================================================

function renderGenres() {

    const genres =
        spotifyData.genres[currentPeriod];


    const container =
        document.getElementById("genres-list");


    container.innerHTML = "";


    genres.forEach((genre) => {

        const item = document.createElement("div");

        item.className = "genre-item";


        item.innerHTML = `

            <span class="genre-name">
                ${escapeHTML(genre.name)}
            </span>

            <span class="genre-count">
                ${genre.count}
            </span>

        `;


        container.appendChild(item);
    });
}


// ============================================================
// ALBUMS
// ============================================================

function renderAlbums() {

    const albumsData =
        spotifyData.albums[currentPeriod];

    const albums = albumsData.albums;


    const container =
        document.getElementById("albums-list");


    container.innerHTML = "";


    albums.forEach((album) => {

        const item = document.createElement("article");

        item.className = "album-card";


        item.innerHTML = `

            <img
                class="album-image"
                src="${album.image || ""}"
                alt=""
            >

            <div class="album-info">

                <div class="album-name">
                    ${escapeHTML(album.album)}
                </div>

                <div class="album-artist">
                    ${escapeHTML(album.artists)}
                </div>

            </div>

        `;


        container.appendChild(item);
    });
}


// ============================================================
// PLAYLISTS
// ============================================================

function renderPlaylists() {

    const playlistData =
        spotifyData.playlists;


    document.getElementById(
        "playlist-total"
    ).textContent =
        playlistData.total;


    document.getElementById(
        "playlist-total-tracks"
    ).textContent =
        playlistData.total_tracks;


    document.getElementById(
        "playlist-average-tracks"
    ).textContent =
        playlistData.average_tracks;


    const container =
        document.getElementById("playlists-list");


    container.innerHTML = "";


    playlistData.playlists.forEach((playlist) => {

        const item = document.createElement("article");

        item.className = "playlist-card";


        item.innerHTML = `

            <img
                class="playlist-image"
                src="${playlist.image || ""}"
                alt=""
            >

            <div class="playlist-info">

                <div class="playlist-name">
                    ${escapeHTML(playlist.name)}
                </div>

                <div class="playlist-tracks">
                    ${playlist.tracks} tracks
                </div>

            </div>

        `;


        container.appendChild(item);
    });
}


// ============================================================
// PERIOD COMPARISON
// ============================================================

function renderComparison() {

    const artists =
        spotifyData.comparison.artists;

    const tracks =
        spotifyData.comparison.tracks;


    document.getElementById(
        "comparison-artists-short"
    ).textContent =
        artists.short_term.total;


    document.getElementById(
        "comparison-artists-medium"
    ).textContent =
        artists.medium_term.total;


    document.getElementById(
        "comparison-artists-long"
    ).textContent =
        artists.long_term.total;


    document.getElementById(
        "comparison-tracks-short"
    ).textContent =
        tracks.short_term.total;


    document.getElementById(
        "comparison-tracks-medium"
    ).textContent =
        tracks.medium_term.total;


    document.getElementById(
        "comparison-tracks-long"
    ).textContent =
        tracks.long_term.total;
}


// ============================================================
// CONSISTENCY
// ============================================================

function renderConsistency() {

    const crossPeriod =
        spotifyData.cross_period;


    document.getElementById(
        "repeated-artists"
    ).textContent =
        crossPeriod.artist_stability
            .artists_in_multiple_periods;


    document.getElementById(
        "repeated-tracks"
    ).textContent =
        crossPeriod.track_stability
            .tracks_in_multiple_periods;
}


// ============================================================
// PERIOD BUTTONS
// ============================================================

function setupPeriodButtons() {

    const buttons =
        document.querySelectorAll(
            ".period-button"
        );


    buttons.forEach((button) => {

        button.addEventListener(
            "click",
            () => {

                currentPeriod =
                    button.dataset.period;


                buttons.forEach(
                    (otherButton) => {

                        otherButton.classList.remove(
                            "active"
                        );
                    }
                );


                button.classList.add(
                    "active"
                );


                renderArtists();

                renderTracks();

                renderGenres();

                renderAlbums();
            }
        );
    });
}


// ============================================================
// NUMBER FORMATTING
// ============================================================

function formatNumber(number) {

    return new Intl.NumberFormat(
        "en-US"
    ).format(number);
}


// ============================================================
// HTML SAFETY
// ============================================================

function escapeHTML(value) {

    if (value === null || value === undefined) {
        return "";
    }


    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


// ============================================================
// INITIALIZATION
// ============================================================

setupPeriodButtons();

loadSpotifyData();