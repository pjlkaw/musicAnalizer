let currentTab = "top-artists";
let currentTimeRange = "medium_term";

document.addEventListener("DOMContentLoaded", () => {
    setupNavigation();
    fetchUserProfile();
    loadTabData();
});

function setupNavigation() {
    const navButtons = document.querySelectorAll("nav button");
    navButtons.forEach(button => {
        button.addEventListener("click", () => {
            const tab = button.getAttribute("data-tab");
            switchTab(tab, button);
        });
    });
}

async function fetchUserProfile() {
    try {
        const res = await fetch("/me");

        if (res.status === 401) {
            renderUnauthenticated();
            return;
        }

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || "Erro ao carregar perfil.");
        }

        document.getElementById("user-name").textContent = data.name || data.id || "Usuário";

        if (data.image) {
            document.getElementById("user-avatar").src = data.image;
        }
    } catch (err) {
        console.error("Erro ao carregar perfil:", err);
        document.getElementById("user-name").textContent = "Erro ao carregar";
    }
}

function renderUnauthenticated() {
    document.querySelector("main").innerHTML = `
        <div class="login-prompt">
            <h2>Sessão não autenticada</h2>
            <p>Faça login com sua conta do Spotify para visualizar seus dados.</p>
            <a href="/" class="login-btn">Fazer Login no Spotify</a>
        </div>
    `;
}

function switchTab(tab, button) {
    currentTab = tab;

    document.querySelectorAll("nav button").forEach(btn => {
        btn.classList.remove("active");
    });

    button.classList.add("active");

    const titles = {
        "top-artists": "Top Artistas",
        "top-tracks": "Top Músicas",
        "recently-played": "Tocadas Recentemente",
        "saved-tracks": "Músicas Salvas",
        "saved-albums": "Álbuns Salvos",
        "playlists": "Minhas Playlists"
    };

    document.getElementById("page-title").textContent = titles[tab] || "Dashboard";
    loadTabData();
}

function loadTabData() {
    const content = document.getElementById("content-container");
    const stats = document.getElementById("stats-container");
    const genres = document.getElementById("genres-container");
    const controls = document.getElementById("controls-container");

    content.innerHTML = '<div class="loading">Carregando...</div>';
    stats.innerHTML = "";
    genres.innerHTML = "";
    controls.innerHTML = "";

    if (currentTab === "top-artists" || currentTab === "top-tracks") {
        controls.innerHTML = `
            <label for="timeRange">Período:</label>
            <select id="timeRange" class="time-range-select">
                <option value="short_term" ${currentTimeRange === "short_term" ? "selected" : ""}>Últimas 4 semanas</option>
                <option value="medium_term" ${currentTimeRange === "medium_term" ? "selected" : ""}>Últimos 6 meses</option>
                <option value="long_term" ${currentTimeRange === "long_term" ? "selected" : ""}>Todo o histórico</option>
            </select>
        `;

        document.getElementById("timeRange").addEventListener("change", (e) => {
            changeTimeRange(e.target.value);
        });
    }

    switch (currentTab) {
        case "top-artists":
            fetchTopArtists();
            break;
        case "top-tracks":
            fetchTopTracks();
            break;
        case "recently-played":
            fetchRecentlyPlayed();
            break;
        case "saved-tracks":
            fetchSavedTracks();
            break;
        case "saved-albums":
            fetchSavedAlbums();
            break;
        case "playlists":
            fetchPlaylists();
            break;
    }
}

function changeTimeRange(value) {
    currentTimeRange = value;
    loadTabData();
}

async function fetchTopArtists() {
    try {
        const res = await fetch(`/top/artists?time_range=${currentTimeRange}`);
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || "Erro ao carregar artistas.");
        }

        renderStats([
            { label: "Artistas Carregados", value: data.total ?? 0 },
        ]);

        renderGrid(data.artists, item => ({
            title: item.name || "Artista sem nome",
            subtitle: item.genres?.slice(0, 2).join(", ") || "Artista",
            image: item.image,
            url: item.spotify_url,
            badge: `#${item.position ?? "-"}`
        }));
    } catch (err) {
        renderError(err);
    }
}

async function fetchTopTracks() {
    try {
        const res = await fetch(`/top/tracks?time_range=${currentTimeRange}`);
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || "Erro ao carregar músicas.");
        }

        renderStats([
            { label: "Músicas Carregadas", value: data.total ?? 0 },
            { label: "Artistas Únicos", value: data.unique_artists ?? 0 },
            { label: "Álbuns Únicos", value: data.unique_albums ?? 0 }
        ]);

        renderGrid(data.tracks, item => ({
            title: item.name || "Música sem nome",
            subtitle: `${item.artists || "Artista desconhecido"} • ${item.album || "Álbum desconhecido"}`,
            image: item.image,
            url: item.spotify_url,
            badge: `#${item.position ?? "-"}`
        }));
    } catch (err) {
        renderError(err);
    }
}

async function fetchRecentlyPlayed() {
    try {
        const res = await fetch("/recently-played");
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || "Erro ao carregar histórico.");
        }

        renderStats([
            { label: "Reproduções Registradas", value: data.total ?? 0 },
            { label: "Músicas Únicas", value: data.unique_tracks ?? 0 },
            { label: "Artistas Únicos", value: data.unique_artists ?? 0 }
        ]);

        renderGrid(data.history, item => ({
            title: item.name || "Música sem nome",
            subtitle: `${item.artists || "Artista desconhecido"} • ${formatPlayedAt(item.played_at)}`,
            image: item.image,
            url: item.spotify_url
        }));
    } catch (err) {
        renderError(err);
    }
}

async function fetchSavedTracks() {
    try {
        const res = await fetch("/saved/tracks");
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || "Erro ao carregar músicas salvas.");
        }

        renderStats([
            { label: "Total Salvo", value: data.total ?? 0 },
            { label: "Artistas Únicos", value: data.unique_artists ?? 0 },
            { label: "Álbuns Únicos", value: data.unique_albums ?? 0 }
        ]);

        renderGrid(data.tracks, item => ({
            title: item.name || "Música sem nome",
            subtitle: `${item.artists || "Artista desconhecido"} • ${item.album || "Álbum desconhecido"}`,
            image: item.image,
            url: item.spotify_url
        }));
    } catch (err) {
        renderError(err);
    }
}

async function fetchSavedAlbums() {
    try {
        const res = await fetch("/saved/albums");
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || "Erro ao carregar álbuns salvos.");
        }

        renderStats([
            { label: "Total Salvo", value: data.total ?? 0 },
            { label: "Artistas Únicos", value: data.unique_artists ?? 0 },
            { label: "Álbuns Carregados", value: data.loaded ?? 0 }
        ]);

        renderGrid(data.albums, item => ({
            title: item.name || "Álbum sem nome",
            subtitle: `${item.artists || "Artista desconhecido"} • ${item.total_tracks ?? 0} faixas`,
            image: item.image,
            url: item.spotify_url
        }));
    } catch (err) {
        renderError(err);
    }
}

async function fetchPlaylists() {
    try {
        const res = await fetch("/playlists");
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || "Erro ao carregar playlists.");
        }

        renderStats([
            { label: "Total de Playlists", value: data.total ?? 0 },
            { label: "Faixas nas Playlists", value: data.total_items ?? 0 },
            { label: "Média de Faixas", value: data.average_items ?? 0 }
        ]);

        renderGrid(data.playlists, item => ({
            title: item.name || "Playlist sem nome",
            subtitle: `${item.items ?? 0} faixas ${item.public ? "• Pública" : "• Privada"}`,
            image: item.image,
            url: item.spotify_url
        }));
    } catch (err) {
        renderError(err);
    }
}

function renderStats(statsArray) {
    const container = document.getElementById("stats-container");

    container.innerHTML = `
        <div class="stats-container">
            ${statsArray.map(stat => `
                <div class="stat-card">
                    <div class="stat-value">${escapeHTML(String(stat.value ?? 0))}</div>
                    <div class="stat-label">${escapeHTML(stat.label)}</div>
                </div>
            `).join("")}
        </div>
    `;
}

function renderGrid(items, mapFn) {
    const container = document.getElementById("content-container");

    if (!items || items.length === 0) {
        container.innerHTML = '<div class="loading">Nenhum dado encontrado.</div>';
        return;
    }

    const defaultImg = "https://via.placeholder.com/300/282828/b3b3b3?text=Sem+Imagem";

    const cardsHTML = items.map(rawItem => {
        const item = mapFn(rawItem);

        const title = item.title || "Sem nome";
        const subtitle = item.subtitle || "";
        const image = item.image || defaultImg;
        const url = item.url || "";
        const badge = item.badge || "";

        return `
            <a href="${url || "#"}" ${url ? 'target="_blank" rel="noopener noreferrer"' : ""} class="card">
                ${badge ? `<div class="card-badge">${escapeHTML(badge)}</div>` : ""}
                <div class="card-img-wrapper">
                    <img src="${escapeHTML(image)}" alt="${escapeHTML(title)}" loading="lazy">
                </div>
                <div class="card-title">${escapeHTML(title)}</div>
                <div class="card-subtitle">${escapeHTML(subtitle)}</div>
            </a>
        `;
    }).join("");

    container.innerHTML = `<div class="cards-grid">${cardsHTML}</div>`;
}

function renderError(error) {
    console.error(error);

    document.getElementById("content-container").innerHTML = `
        <div class="error">
            <h2>Não foi possível carregar os dados</h2>
            <p>${escapeHTML(error.message || "Erro desconhecido.")}</p>
        </div>
    `;
}

function formatPlayedAt(value) {
    if (!value) {
        return "Horário desconhecido";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "Horário desconhecido";
    }

    return date.toLocaleString("pt-BR", {
        dateStyle: "short",
        timeStyle: "short"
    });
}

function escapeHTML(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}