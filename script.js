let sfxData = [];
let fuse;

console.log("Initializing Sound Library...");

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

        // Fuse.js Search Configuration
        fuse = new Fuse(sfxData, {
            keys: ['n', 'p'],
            threshold: 0.1,          
            ignoreLocation: true,    
            useExtendedSearch: true  
        });

        // Show initial results on load (passing 'false' to indicate it's not an active search)
        displayResults(sfxData.slice(0, 50), false);
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
if (searchInput) {
    searchInput.addEventListener('input', e => {
        const query = e.target.value;
        if (!fuse) return;
        
        // If search is empty or 1 letter, show default batch
        if (query.length < 2) {
            displayResults(sfxData.slice(0, 50), false);
            return;
        }
        
        // Search the entire library
        const results = fuse.search(query).map(r => r.item);
        
        // Pass 'true' to indicate this is an active search
        displayResults(results, true); 
    });
}

function displayResults(items, isSearch = false) {
    const container = document.getElementById('results');
    if (!container) return;

    if (items.length === 0) {
        container.innerHTML = "<p style='padding:20px; color:#666;'>No sounds found. Try a broader search term or different modifier.</p>";
        return;
    }

    // --- NEW: Generate the result summary text ---
    let summaryHtml = "";
    if (isSearch) {
        // Formats the number with commas (e.g., 1,234) and handles pluralization
        summaryHtml = `<div style="width: 100%; max-width: 900px; text-align: left; color: var(--text-muted); font-size: 0.85em; margin-bottom: 5px; padding-left: 5px; font-weight: bold;">Found ${items.length.toLocaleString()} result${items.length === 1 ? '' : 's'}</div>`;
    } else {
        summaryHtml = `<div style="width: 100%; max-width: 900px; text-align: left; color: var(--text-muted); font-size: 0.85em; margin-bottom: 5px; padding-left: 5px; font-style: italic;">Showing a sample of 50 sounds. Use the search bar to find more!</div>`;
    }

    // Generate the HTML for the sound cards
    const cardsHtml = items.map(item => {
        const ext = item.n.split('.').pop().toUpperCase();

        const baseUrl = "https://sinclaircc-my.sharepoint.com/personal/adam_thompson7572_sinclair_edu/Documents/";
        const encodedPath = encodeURIComponent(item.p); 
        const originalUrl = baseUrl + encodedPath;

        const previewUrl = originalUrl + "?download=1";
        const dlUrl = `https://sinclaircc-my.sharepoint.com/personal/adam_thompson7572_sinclair_edu/_layouts/15/download.aspx?SourceUrl=${originalUrl}`;

        return `
            <div class="card">
                <div class="info">
                    <div class="title-row">
                        <span class="file-badge">${ext}</span>
                        <span class="name" title="${item.n}">${item.n}</span>
                    </div>
                    <div class="path">${item.p}</div>
                </div>
                <div class="actions">
                    <a href="${previewUrl}" target="_blank" class="dl-btn preview-btn">▶ Preview</a>
                    <a href="${dlUrl}" class="dl-btn">⬇ Download</a>
                </div>
            </div>
        `;
    }).join('');

    // Combine the summary text and the cards, then inject into the page
    container.innerHTML = summaryHtml + cardsHtml;

    // Jump back to the top of the scroll area
    container.scrollTop = 0;
}
