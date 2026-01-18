let allCoins = [];

function parseNumber(str) {
    if (!str) return 0;
    return parseInt(str.replace(/[$,]/g, '')) || 0;
}

function filterCoins() {
    const pcgsNum = document.getElementById('filterPcgsNum').value.trim().toLowerCase();
    const priceRange = document.getElementById('filterPrice').value;
    const popRange = document.getElementById('filterPopulation').value;
    const mintageRange = document.getElementById('filterMintage').value;

    let filtered = allCoins.filter(coin => {
        // PCGS# filter
        if (pcgsNum && !(coin.pcgs_number || '').toLowerCase().includes(pcgsNum)) {
            return false;
        }

        // Price filter
        if (priceRange) {
            const price = parseNumber(coin.price_guide_value);
            if (priceRange === '0-100' && (price < 0 || price > 100)) return false;
            if (priceRange === '100-500' && (price < 100 || price > 500)) return false;
            if (priceRange === '500-1000' && (price < 500 || price > 1000)) return false;
            if (priceRange === '1000+' && price < 1000) return false;
        }

        // Population filter
        if (popRange) {
            const pop = parseNumber(coin.population);
            if (popRange === '0-1000' && pop > 1000) return false;
            if (popRange === '1000-10000' && (pop < 1000 || pop > 10000)) return false;
            if (popRange === '10000-100000' && (pop < 10000 || pop > 100000)) return false;
            if (popRange === '100000+' && pop < 100000) return false;
        }

        // Mintage filter
        if (mintageRange) {
            const mintage = parseNumber(coin.mintage);
            if (mintageRange === '0-100000' && mintage > 100000) return false;
            if (mintageRange === '100000-1000000' && (mintage < 100000 || mintage > 1000000)) return false;
            if (mintageRange === '1000000-10000000' && (mintage < 1000000 || mintage > 10000000)) return false;
            if (mintageRange === '10000000+' && mintage < 10000000) return false;
        }

        return true;
    });

    renderCoins(filtered);
}

function resetFilters() {
    document.getElementById('filterPcgsNum').value = '';
    document.getElementById('filterPrice').value = '';
    document.getElementById('filterPopulation').value = '';
    document.getElementById('filterMintage').value = '';
    renderCoins(allCoins);
}

function renderCoins(coins) {
    const grid = document.getElementById('coinsGrid');
    const stats = document.getElementById('stats');

    stats.textContent = `Showing ${coins.length} / ${allCoins.length} coins`;

    if (coins.length === 0) {
        grid.innerHTML = '<div class="empty">No matching data</div>';
        return;
    }

    grid.innerHTML = coins.map(coin => `
        <div class="coin-card">
            ${coin.local_image_path ?
                `<img class="coin-image" src="/${coin.local_image_path}" alt="Coin image" />` :
                `<div class="coin-image" style="display:flex;align-items:center;justify-content:center;color:#999;">No image</div>`
            }
            <div class="coin-info">
                <div class="coin-header">
                    <span class="coin-grade">${coin.grade || 'N/A'}</span>
                    <span class="coin-cert">#${coin.cert_number}</span>
                </div>
                <div class="coin-title">${coin.date_mintmark || ''} ${coin.denomination || ''}</div>
                <div class="coin-details">
                    <div class="detail-item">
                        <span class="detail-label">PCGS#</span>
                        <span class="detail-value">${coin.pcgs_number || '-'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Price Guide</span>
                        <span class="detail-value">${coin.price_guide_value || '-'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Population</span>
                        <span class="detail-value">${coin.population || '-'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Mintage</span>
                        <span class="detail-value">${coin.mintage || '-'}</span>
                    </div>
                </div>
                <div class="coin-actions">
                    <button class="btn-delete" onclick="deleteCoin('${coin.cert_number}')">Delete</button>
                </div>
            </div>
        </div>
    `).join('');
}

async function loadCoins() {
    const grid = document.getElementById('coinsGrid');
    const stats = document.getElementById('stats');
    grid.innerHTML = '<div class="loading">Loading...</div>';

    try {
        const response = await fetch('/api/coins');
        const data = await response.json();

        allCoins = data.coins;
        stats.textContent = `Total ${data.total} coins`;

        if (data.coins.length === 0) {
            grid.innerHTML = '<div class="empty">No data yet. Enter a certificate number to scrape.</div>';
            return;
        }

        renderCoins(allCoins);
    } catch (error) {
        grid.innerHTML = '<div class="empty">Failed to load. Please refresh.</div>';
    }
}

async function scrapeCoin() {
    const input = document.getElementById('certInput');
    const btn = document.getElementById('scrapeBtn');
    const certNumber = input.value.trim();

    if (!certNumber) {
        showMessage('Please enter a certificate number', 'error');
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Scraping...';

    try {
        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cert_number: certNumber })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage(`Scraped successfully: ${certNumber}`, 'success');
            input.value = '';
            loadCoins();
        } else {
            showMessage(`Scrape failed: ${data.detail}`, 'error');
        }
    } catch (error) {
        showMessage('Network error. Please retry.', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Scrape';
    }
}

async function deleteCoin(certNumber) {
    if (!confirm(`Are you sure you want to delete certificate ${certNumber}?`)) return;

    try {
        const response = await fetch(`/api/coins/${certNumber}`, { method: 'DELETE' });
        if (response.ok) {
            showMessage('Deleted successfully', 'success');
            loadCoins();
        } else {
            showMessage('Delete failed', 'error');
        }
    } catch (error) {
        showMessage('Network error', 'error');
    }
}

function showMessage(text, type) {
    const msg = document.getElementById('message');
    msg.className = `message ${type}`;
    msg.textContent = text;
    setTimeout(() => { msg.textContent = ''; msg.className = ''; }, 3000);
}

// Enter key triggers scrape
document.getElementById('certInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') scrapeCoin();
});

// Load data on page load
loadCoins();
