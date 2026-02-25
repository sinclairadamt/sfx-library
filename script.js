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

        fuse = new Fuse(sfxData, {
            keys: ['n', 'p'],
            threshold: 0.3,
            distance: 100,
            ignoreLocation: true
        });

        displayResults(sfxData.slice(0, 20));
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
        if (query.length < 2) {
            displayResults(sfxData.slice(0, 20));
            return;
        }
        const results = fuse.search(query).map(r => r.item);
        displayResults(results.slice(0, 100)); 
    });
}

function displayResults(items) {
    const container = document.getElementById('results');
    if (!container) return;

    if (items.length === 0) {
        container.innerHTML = "<p style='padding:20px; color:#666;'>No sounds found. Try a broader search term.</p>";
        return;
    }

    container.innerHTML = items.map(item => {
        const ext = item.n.split('.').pop().toUpperCase();

        // 1. Reconstruct the original SharePoint URL
        const baseUrl = "https://sinclaircc-my.sharepoint.com/personal/adam_thompson7572_sinclair_edu/Documents/";
        
        // encodeURIComponent turns spaces into %20 and slashes into %2F, matching Microsoft's format exactly
        const encodedPath = encodeURIComponent(item.p); 
        const originalUrl = baseUrl + encodedPath;

        // 2. Build the functional links
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

    container.scrollTop = 0;
}