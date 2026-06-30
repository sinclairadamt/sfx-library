let sfxData = [];
let fuse;

const fuseOptions = {
    keys: [
        { name: 'n',    weight: 0.35 },
        { name: 'kw',   weight: 0.30 },
        { name: 'tags', weight: 0.20 },
        { name: 'cat',  weight: 0.10 },
        { name: 'pk',   weight: 0.10 },
        { name: 'src',  weight: 0.05 },
    ],
    threshold: 0.15,
    ignoreLocation: true,
    useExtendedSearch: true,
    minMatchCharLength: 2,
};

const filters = { query: '', category: null, provider: null };

const CAT_COLORS = {
    explosion:        '#dc3545',
    impact:           '#fd7e14',
    weapon:           '#842029',
    foley:            '#795548',
    footsteps:        '#a08060',
    animal:           '#198754',
    human:            '#20c997',
    fire:             '#e25822',
    weather:          '#0dcaf0',
    vehicle:          '#4a90d9',
    scifi:            '#6610f2',
    ui:               '#6366f1',
    music:            '#d63384',
    drone:            '#5a23a5',
    cinematic:        '#b08000',
    horror:           '#343a40',
    cartoon:          '#7aaa00',
    nature:           '#2d9b27',
    mechanical:       '#6c757d',
    electricity:      '#ccaa00',
    glass:            '#5baab8',
    household:        '#c19a6b',
    sports:           '#28a745',
    magic:            '#7952b3',
    underwater:       '#0077be',
    impulse_response: '#0d9488',
    instrument:       '#9c27b0',
    ambience:         '#3a7abd',
    other:            '#999999',
};

console.log("Initializing Sound Library...");

function getRandomItems(arr, count) {
    const shuffled = [...arr].sort(() => 0.5 - Math.random());
    return shuffled.slice(0, count);
}

const CAT_LABELS = {
    scifi:            'Sci-Fi',
    ui:               'UI',
    impulse_response: 'Impulse Response',
};

function catLabel(c) {
    return CAT_LABELS[c] || c.replace(/_/g, ' ').replace(/\b\w/g, ch => ch.toUpperCase());
}

function formatDur(s) {
    if (s < 1)  return '<1s';
    if (s < 60) return Math.round(s) + 's';
    const m = Math.floor(s / 60);
    const sec = Math.round(s % 60);
    return m + ':' + String(sec).padStart(2, '0');
}

function getResults() {
    let pool = sfxData;

    if (filters.category) pool = pool.filter(e => e.cat === filters.category);
    if (filters.provider) pool = pool.filter(e => e.src === filters.provider);

    const query = filters.query.trim();
    const hasPreFilters = !!(filters.category || filters.provider);

    if (query.length < 2) {
        if (hasPreFilters) return pool;
        return getRandomItems(pool, 50);
    }

    if (pool === sfxData && fuse) {
        return fuse.search(query).map(r => r.item);
    }
    return new Fuse(pool, fuseOptions).search(query).map(r => r.item);
}

function buildFilters() {
    const catCounts = {};
    const srcCounts = {};
    sfxData.forEach(e => {
        const c = e.cat || 'other';
        catCounts[c] = (catCounts[c] || 0) + 1;
        if (e.src) srcCounts[e.src] = (srcCounts[e.src] || 0) + 1;
    });

    const cats = Object.entries(catCounts).sort((a, b) => b[1] - a[1]);
    const srcs = Object.entries(srcCounts).sort((a, b) => b[1] - a[1]);

    const catSelect = document.getElementById('cat-select');
    if (catSelect) {
        cats.forEach(([c, count]) => {
            const opt = document.createElement('option');
            opt.value = c;
            opt.textContent = `${catLabel(c)} (${count.toLocaleString()})`;
            catSelect.appendChild(opt);
        });
        catSelect.addEventListener('change', () => {
            filters.category = catSelect.value || null;
            refreshResults();
        });
    }

    const srcSelect = document.getElementById('src-select');
    if (srcSelect) {
        srcs.forEach(([s, count]) => {
            const opt = document.createElement('option');
            opt.value = s;
            opt.textContent = `${s} (${count.toLocaleString()})`;
            srcSelect.appendChild(opt);
        });
        srcSelect.addEventListener('change', () => {
            filters.provider = srcSelect.value || null;
            refreshResults();
        });
    }
}

function refreshResults() {
    filters.query = searchInput ? searchInput.value : '';
    const hasActivity = filters.query.trim().length >= 2 || filters.category || filters.provider;
    displayResults(getResults(), !!hasActivity);
}

fetch('data.json')
    .then(response => {
        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        return response.json();
    })
    .then(data => {
        sfxData = data;
        console.log("Successfully loaded " + data.length + " records.");

        const stats = document.getElementById('stats');
        if (stats) stats.innerText = `Library Loaded: ${data.length.toLocaleString()} Sounds`;

        fuse = new Fuse(sfxData, fuseOptions);

        buildFilters();
        displayResults(getRandomItems(sfxData, 50), false);
    })
    .catch(err => {
        console.error("Initialization Failed:", err);
        document.getElementById('results').innerHTML = `
            <div style="padding: 20px; color: #721c24; background: #f8d7da; border-radius: 8px; margin: 20px; text-align: center;">
                <strong>Error Loading Library:</strong> ${err.message}
            </div>
        `;
    });

const searchInput = document.getElementById('searchInput');
const clearBtn    = document.getElementById('clearSearch');
const searchBtn   = document.getElementById('searchBtn');

function executeSearch() {
    if (!fuse) return;

    filters.query = searchInput.value;

    if (filters.query.length < 2 && !filters.category && !filters.provider && !filters.duration) {
        displayResults(getRandomItems(sfxData, 50), false);
        return;
    }

    const container = document.getElementById('results');
    container.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:center;gap:15px;padding:40px;color:var(--text-muted);font-size:1.1em;font-weight:bold;width:100%;">
            <div class="spinner"></div> Searching library...
        </div>
    `;

    setTimeout(() => {
        displayResults(getResults(), true);
    }, 50);
}

if (searchInput) {
    searchInput.addEventListener('input', e => {
        clearBtn.style.display = e.target.value.length > 0 ? 'block' : 'none';
    });

    searchInput.addEventListener('keypress', e => {
        if (e.key === 'Enter') {
            e.preventDefault();
            executeSearch();
        }
    });
}

if (searchBtn)  searchBtn.addEventListener('click', executeSearch);

if (clearBtn) {
    clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        clearBtn.style.display = 'none';
        filters.query = '';
        refreshResults();
        searchInput.focus();
    });
}

const MAX_DISPLAY = 200;

function displayResults(items, isSearch = false) {
    const container = document.getElementById('results');
    if (!container) return;

    if (items.length === 0) {
        container.innerHTML = "<p style='padding:20px;color:#666;'>No sounds found. Try a broader search term or adjust your filters.</p>";
        return;
    }

    const hasPreFilters = !!(filters.category || filters.provider || filters.duration);
    const total = items.length;
    const displayed = items.slice(0, MAX_DISPLAY);

    let summaryText;
    if (isSearch || hasPreFilters) {
        summaryText = `Found ${total.toLocaleString()} result${total === 1 ? '' : 's'}`;
        if (total > MAX_DISPLAY) summaryText += ` &mdash; showing first ${MAX_DISPLAY}`;
    } else {
        summaryText = `Showing 50 random sounds to spark your creativity. Use the search bar to find more!`;
    }

    const summaryHtml = `<div class="results-summary">${summaryText}</div>`;

    const cardsHtml = displayed.map(item => {
        const ext = item.n.split('.').pop().toUpperCase();
        const lastDot = item.n.lastIndexOf('.');
        const displayName = lastDot !== -1 ? item.n.substring(0, lastDot) : item.n;

        // Use enriched src/pk for path display; fall back to old path stripping
        let displayPath;
        if (item.src && item.pk && item.src !== item.pk) {
            displayPath = `${item.src} &rsaquo; ${item.pk}`;
        } else if (item.src) {
            displayPath = item.src;
        } else {
            let dp = item.p;
            const prefix = "Sinclair/SFX Libraries/";
            if (dp.startsWith(prefix)) dp = dp.slice(prefix.length);
            if (dp.endsWith(item.n)) dp = dp.slice(0, -item.n.length);
            if (dp.endsWith('/')) dp = dp.slice(0, -1);
            displayPath = dp || "Main Folder";
        }

        const baseUrl  = "https://sinclaircc-my.sharepoint.com/personal/adam_thompson7572_sinclair_edu/Documents/";
        const encoded  = encodeURIComponent(item.p);
        const origUrl  = baseUrl + encoded;
        const previewUrl = origUrl + "?download=1";
        const dlUrl    = `https://sinclaircc-my.sharepoint.com/personal/adam_thompson7572_sinclair_edu/_layouts/15/download.aspx?SourceUrl=${origUrl}`;

        const cat      = item.cat || 'other';
        const catColor = CAT_COLORS[cat] || '#999';
        const catName  = catLabel(cat);
        const durBadge = item.dur !== undefined
            ? `<span class="dur-badge">${formatDur(item.dur)}</span>`
            : '';

        return `
            <div class="card" style="border-left-color:${catColor}">
                <div class="info">
                    <div class="title-row">
                        <span class="file-badge">${ext}</span>
                        <span class="cat-badge" style="background:${catColor}">${catName}</span>
                        <span class="name" title="${item.n}">${displayName}</span>
                        ${durBadge}
                    </div>
                    <div class="path">${displayPath}</div>
                </div>
                <div class="actions">
                    <a href="${previewUrl}" target="_blank" class="dl-btn preview-btn">&#9654; Preview</a>
                    <a href="${dlUrl}" class="dl-btn">&#11015; Download</a>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = summaryHtml + cardsHtml;
    container.scrollTop = 0;
}
