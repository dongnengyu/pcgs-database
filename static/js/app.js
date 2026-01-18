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

    stats.textContent = `显示 ${coins.length} / ${allCoins.length} 枚硬币`;

    if (coins.length === 0) {
        grid.innerHTML = '<div class="empty">无匹配数据</div>';
        return;
    }

    grid.innerHTML = coins.map(coin => `
        <div class="coin-card">
            <div class="coin-content">
                <div class="coin-info">
                    <div class="coin-title">${coin.date_mintmark || ''} ${coin.denomination || ''} ${coin.variety || ''}</div>
                    <div class="coin-cert">#${coin.cert_number}</div>
                    <table class="coin-details">
                        <tr>
                            <td class="detail-label">等级</td>
                            <td class="detail-value">${coin.grade || '-'}</td>
                        </tr>
                        <tr>
                            <td class="detail-label">PCGS 编号</td>
                            <td class="detail-value">${coin.pcgs_number || '-'}</td>
                        </tr>
                        <tr>
                            <td class="detail-label">PCGS价格指南价值</td>
                            <td class="detail-value">${coin.price_guide_value || '-'}</td>
                        </tr>
                        <tr>
                            <td class="detail-label">日期, 造币厂厂标</td>
                            <td class="detail-value">${coin.date_mintmark || '-'}</td>
                        </tr>
                        <tr>
                            <td class="detail-label">面额</td>
                            <td class="detail-value">${coin.denomination || '-'}</td>
                        </tr>
                        <tr>
                            <td class="detail-label">数量</td>
                            <td class="detail-value">${coin.population || '-'}</td>
                        </tr>
                        <tr>
                            <td class="detail-label">高评级数量</td>
                            <td class="detail-value">${coin.pop_higher || '-'}</td>
                        </tr>
                        <tr>
                            <td class="detail-label">版别</td>
                            <td class="detail-value">${coin.variety || '-'}</td>
                        </tr>
                        <tr>
                            <td class="detail-label">地区</td>
                            <td class="detail-value">${coin.region || '-'}</td>
                        </tr>
                        <tr>
                            <td class="detail-label">安全保障</td>
                            <td class="detail-value">${coin.security || '-'}</td>
                        </tr>
                        <tr>
                            <td class="detail-label">包装盒类型</td>
                            <td class="detail-value">${coin.holder_type || '-'}</td>
                        </tr>
                    </table>
                    <div class="coin-actions">
                        <button class="btn-delete" onclick="deleteCoin('${coin.cert_number}')">删除</button>
                    </div>
                </div>
                <div class="coin-image-wrapper">
                    ${coin.local_image_path ?
                        `<img class="coin-image" src="/${coin.local_image_path}" alt="硬币图片" />` :
                        `<div class="coin-image no-image">无图片</div>`
                    }
                </div>
            </div>
        </div>
    `).join('');
}

async function loadCoins() {
    const grid = document.getElementById('coinsGrid');
    const stats = document.getElementById('stats');
    grid.innerHTML = '<div class="loading">加载中...</div>';

    try {
        const response = await fetch('/api/coins');
        const data = await response.json();

        allCoins = data.coins;
        stats.textContent = `共 ${data.total} 枚硬币`;

        if (data.coins.length === 0) {
            grid.innerHTML = '<div class="empty">暂无数据，请输入证书号抓取</div>';
            return;
        }

        renderCoins(allCoins);
    } catch (error) {
        grid.innerHTML = '<div class="empty">加载失败，请刷新重试</div>';
    }
}

async function scrapeCoin() {
    const input = document.getElementById('certInput');
    const btn = document.getElementById('scrapeBtn');
    const certNumber = input.value.trim();

    if (!certNumber) {
        showMessage('请输入证书号', 'error');
        return;
    }

    btn.disabled = true;
    btn.textContent = '抓取中...';

    try {
        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cert_number: certNumber })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage(`抓取成功: ${certNumber}`, 'success');
            input.value = '';
            loadCoins();
        } else {
            showMessage(`抓取失败: ${data.detail}`, 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '抓取';
    }
}

async function deleteCoin(certNumber) {
    if (!confirm(`确定删除证书号 ${certNumber} 吗？`)) return;

    try {
        const response = await fetch(`/api/coins/${certNumber}`, { method: 'DELETE' });
        if (response.ok) {
            showMessage('删除成功', 'success');
            loadCoins();
        } else {
            showMessage('删除失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误', 'error');
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
