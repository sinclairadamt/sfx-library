let sfxData = [];
let fuse;

console.log("Initializing Sound Library...");

// --- NEW: Helper function to grab 50 random sounds ---
function getRandomItems(arr, count) {
    // Shuffles a copy of the array and slices off the desired amount
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

        // Load 50 random sounds to start
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
const clearBtn = document.getElementById('clearSearch'); // Select the X button

if (searchInput) {
    searchInput.addEventListener('input', e => {
        const query = e.target.value;
        
        // Show or hide the clear button based on input length
        if (query.length > 0) {
            clearBtn.style.display = 'block';
        } else {
            clearBtn.style.display = 'none';
        }

        if (!fuse) return;
        
        // If search is empty or 1 letter, show 50 random items
        if (query.length < 2) {
            displayResults(getRandomItems(sfxData, 50), false);
            return;
        }
        
        // Active search
        const results = fuse.search(query).map(r => r.item);
        displayResults(results, true); 
    });
}

// --- NEW: Event listener for the clear button ---
if (clearBtn) {
    clearBtn.addEventListener('click', () => {
        searchInput.value = '';             // Empty the text
        clearBtn.style.display = 'none';    // Hide the X
        displayResults(getRandomItems(sfxData, 50), false); // Reshuffle 50 sounds
        searchInput.focus();                // Put the typing cursor back in the box
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
        // Updated text to reflect the new random behavior
        summaryHtml = `<div style="width: 100%; max-width: 900px; text-align: left; color: var(--text-muted); font-size: 0.85em; margin-bottom: 5px; padding-left: 5px; font-style: italic;">Showing 50 random sounds to spark your creativity. Use the search bar to find more!</div>`;
    }

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

    container.innerHTML = summaryHtml + cardsHtml;
    container.scrollTop = 0;
}
