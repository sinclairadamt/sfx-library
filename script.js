let sfxData = [];
let fuse;

console.log("Initializing Sound Library...");

function getRandomItems(arr, count) {
    const shuffled = [...arr].sort(() => 0.5 - Math.random());
    return shuffled.slice(0, count);
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

        fuse = new Fuse(sfxData, {
            keys: ['n', 'p'],
            threshold: 0.1,          
            ignoreLocation: true,    
            useExtendedSearch: true  
        });

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
const clearBtn = document.getElementById('clearSearch'); 

if (searchInput) {
    searchInput.addEventListener('input', e => {
        const query = e.target.value;
        
        if (query.length > 0) {
            clearBtn.style.display = 'block';
        } else {
            clearBtn.style.display = 'none';
        }

        if (!fuse) return;
        
        if (query.length < 2) {
            displayResults(getRandomItems(sfxData, 50), false);
            return;
        }
        
        const results = fuse.search(query).map(r => r.item);
        displayResults(results, true); 
    });
}

if (clearBtn) {
    clearBtn.addEventListener('click', () => {
        searchInput.value = '';             
        clearBtn.style.display = 'none';    
        displayResults(getRandomItems(sfxData, 50), false); 
        searchInput.focus();                
    });
}

function displayResults(items, isSearch = false) {
    const container = document.getElementById('results');
    if (!container) return;

    if (items.length === 0) {
        container.innerHTML = "<p style='padding:20px; color:#666;'>No sounds found. Try a broader search term or different modifier.</p>";
        return;
    }

    let summaryHtml = "";
    if (isSearch) {
        summaryHtml = `<div style="width: 100%; max-width: 900px; text-align: left; color: var(--text-muted); font-size: 0.85em; margin-bottom: 5px; padding-left: 5px; font-weight: bold;">Found ${items.length.toLocaleString()} result${items.length === 1 ? '' : 's'}</div>`;
    } else {
        summaryHtml = `<div style="width: 100%; max-width: 900px; text-align: left; color: var(--text-muted); font-size: 0.85em; margin-bottom: 5px; padding-left: 5px; font-style: italic;">Showing 50 random sounds to spark your creativity. Use the search bar to find more!</div>`;
    }

    const cardsHtml = items.map(item => {
        const ext = item.n.split('.').pop().toUpperCase();

        // --- VISUAL PATH CLEANUP ---
        let displayPath = item.p;
        
        // 1. Remove the Sinclair prefix
        const prefix = "Sinclair/SFX Libraries/";
        if (displayPath.startsWith(prefix)) {
            displayPath = displayPath.slice(prefix.length);
        }
        
        // 2. Remove the filename from the end
        if (displayPath.endsWith(item.n)) {
            displayPath = displayPath.slice(0, -item.n.length);
        }
        
        // 3. Remove trailing slash if it exists
        if (displayPath.endsWith('/')) {
            displayPath = displayPath.slice(0, -1);
        }
        
        // 4. Fallback if the file is sitting right in the root library folder
        if (displayPath === "") {
            displayPath = "Main Folder";
        }
        // ---------------------------

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
                    <div class="path">${displayPath}</div>
                </div>
                <div class="actions">
                    <a href="${previewUrl}" target="_blank" class="dl-btn preview-btn">▶ Preview</a>
                    <a href="${dlUrl}" class="dl-btn">⬇ Download</a>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = summaryHtml + cardsHtml;
    container.scrollTop = 0;
}
