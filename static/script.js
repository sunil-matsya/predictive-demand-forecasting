document.addEventListener('DOMContentLoaded', async () => {
    const monthSelect = document.getElementById('month_select');
    
    // 1. Fetch available months
    try {
        const res = await fetch('/months');
        const data = await res.json();
        if (data.months) {
            data.months.forEach(month => {
                const opt = document.createElement('option');
                opt.value = month;
                opt.textContent = `Month ${month}`;
                monthSelect.appendChild(opt);
            });
        }
    } catch(e) {
        console.error("Failed to fetch months", e);
    }
    
    // 2. Tab Switching Logic
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active from all
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active to clicked
            btn.classList.add('active');
            const target = document.getElementById(btn.dataset.tab);
            target.classList.add('active');
        });
    });

    // 3. Single Prediction form
    document.getElementById('predict-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const shopId = document.getElementById('shop_id').value;
        const itemId = document.getElementById('item_id').value;
        const monthBlock = document.getElementById('month_select').value;
        
        const btnText = document.querySelector('.btn-text');
        const loader = document.querySelector('.loader');
        const resultCard = document.getElementById('result-card');
        const forecastVal = document.getElementById('forecast-value');

        // UI Loading state
        btnText.classList.add('hidden');
        loader.classList.remove('hidden');
        resultCard.classList.add('hidden');
        
        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ shop_id: parseInt(shopId), item_id: parseInt(itemId), month_block: parseInt(monthBlock) })
            });
            
            if (!response.ok) throw new Error('API request failed');
            
            const data = await response.json();
            
            // Counter animation
            animateValue(forecastVal, parseFloat(forecastVal.innerText) || 0, data.forecast_30_days, 1000);
            
            // Show result
            resultCard.classList.remove('hidden');
            
        } catch (err) {
            alert('An error occurred while fetching the forecast.');
            console.error(err);
        } finally {
            btnText.classList.remove('hidden');
            loader.classList.add('hidden');
        }
    });

    // 4. Top Forecasts Logic
    const topBtn = document.getElementById('generate-top-btn');
    const topContainer = document.getElementById('top-table-container');
    const topBody = document.getElementById('top-table-body');
    let topData = [];

    topBtn.addEventListener('click', async () => {
        const monthBlock = document.getElementById('month_select').value;
        
        const btnText = topBtn.querySelector('.btn-text');
        const loader = topBtn.querySelector('.loader');
        
        btnText.classList.add('hidden');
        loader.classList.remove('hidden');
        topContainer.classList.add('hidden');
        topBody.innerHTML = ''; // clear table
        
        try {
            const response = await fetch('/top_predictions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ month_block: parseInt(monthBlock) })
            });
            
            if (!response.ok) throw new Error("API request failed");
            
            const data = await response.json();
            topData = data.top_predictions;
            renderTable(topData);
            topContainer.classList.remove('hidden');
        } catch (err) {
            alert('Error fetching top forecasts.');
            console.error(err);
        } finally {
            btnText.classList.remove('hidden');
            loader.classList.add('hidden');
        }
    });
    
    // 5. Sorting logic
    let currentSort = { col: 'forecast_30_days', asc: false };
    
    const ths = document.querySelectorAll('.glass-table th');
    ths.forEach(th => {
        th.addEventListener('click', () => {
            const rawCol = th.dataset.sort;
            const col = rawCol === 'forecast' ? 'forecast_30_days' : rawCol;
            
            if (currentSort.col === col) {
                currentSort.asc = !currentSort.asc;
            } else {
                currentSort.col = col;
                currentSort.asc = false;
            }
            
            // update icons
            ths.forEach(header => {
                const icon = header.querySelector('.sort-icon');
                icon.className = 'sort-icon';
                if (header.dataset.sort === rawCol) {
                    icon.classList.add(currentSort.asc ? 'asc' : 'desc');
                }
            });
            
            const sorted = [...topData].sort((a, b) => {
                const valA = a[col];
                const valB = b[col];
                if (valA < valB) return currentSort.asc ? -1 : 1;
                if (valA > valB) return currentSort.asc ? 1 : -1;
                return 0;
            });
            
            renderTable(sorted);
        });
    });

    function renderTable(dataArray) {
        topBody.innerHTML = '';
        dataArray.forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${row.shop_id}</td>
                <td>${row.item_id}</td>
                <td><strong>${row.forecast_30_days.toFixed(2)}</strong></td>
            `;
            topBody.appendChild(tr);
        });
    }

});

function animateValue(obj, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const easeProg = 1 - Math.pow(1 - progress, 4);
        obj.innerHTML = (easeProg * (end - start) + start).toFixed(2);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        } else {
            obj.innerHTML = end.toFixed(2);
        }
    };
    window.requestAnimationFrame(step);
}
