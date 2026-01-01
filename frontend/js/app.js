/**
 * Twitter Trends Dashboard - Logic & Charts (CORREGIDO)
 */

const chartInstances = {};
let API_BASE = window.location.origin; // Simplificado para evitar errores de ruta
let lastSpreadData = [];

const countryTranslations = {
    "worldwide": "Global", "united-states": "Estados Unidos", "united-kingdom": "Reino Unido",
    "brazil": "Brasil", "canada": "Canadá", "france": "Francia", "germany": "Alemania",
    "india": "India", "japan": "Japón", "netherlands": "Países Bajos", "peru": "Perú",
    "russia": "Rusia", "sweden": "Suecia", "switzerland": "Suiza", "ecuador": "Ecuador",
    "argentina": "Argentina", "mexico": "México", "colombia": "Colombia", "spain": "España",
    "australia": "Australia"
};

// --- Manejo de Calendarios ---
const inputFrom = document.getElementById('filter-date-from');
const inputTo = document.getElementById('filter-date-to');

inputFrom.addEventListener('change', () => {
    inputTo.min = inputFrom.value;
    if (inputTo.value < inputFrom.value) inputTo.value = inputFrom.value;
});

inputTo.addEventListener('change', () => {
    inputFrom.max = inputTo.value;
    if (inputFrom.value > inputTo.value) inputFrom.value = inputTo.value;
});

// --- Utilidades de Tiempo ---
function formatToLocalTime(isoString, showTime = true) {
    if (!isoString) return "--:--";
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return isoString;
    const options = { day: '2-digit', month: 'short' };
    if (showTime) { options.hour = '2-digit'; options.minute = '2-digit'; options.hour12 = false; }
    return date.toLocaleDateString('es-ES', options);
}

function getLocalTodayString() {
    return new Date().toISOString().split('T')[0];
}

function getUTCRange() {
    const dFrom = document.getElementById('filter-date-from').value; 
    const dTo = document.getElementById('filter-date-to').value;
    return { from: `${dFrom}T00:00:00`, to: `${dTo}T23:59:59` };
}

function getAutoGranularity(dateFrom, dateTo) {
    const diffDays = Math.ceil(Math.abs(new Date(dateTo) - new Date(dateFrom)) / (1000 * 60 * 60 * 24));
    return diffDays <= 2 ? 'hour' : 'day';
}

const chartOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { position: 'top', labels: { boxWidth: 10, font: { size: 11 } } } },
    scales: { y: { beginAtZero: true, grid: { color: '#f1f5f9' } }, x: { grid: { display: false } } }
};

// --- Renders de Gráficas ---
function drawActivity(data, granularity) {
    const ctx = document.getElementById('chart-activity').getContext('2d');
    if (chartInstances.activity) chartInstances.activity.destroy();
    chartInstances.activity = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => formatToLocalTime(d.timestamp, granularity === 'hour')),
            datasets: [{
                label: 'Tendencias Únicas',
                data: data.map(d => d.total_trends),
                borderColor: '#2563eb', backgroundColor: 'rgba(37, 99, 235, 0.1)', fill: true, tension: 0.3
            }]
        },
        options: chartOptions
    });
}

function drawIntensity(data) {
    const ctx = document.getElementById('chart-intensity').getContext('2d');
    if (chartInstances.intensity) chartInstances.intensity.destroy();
    chartInstances.intensity = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.trend),
            datasets: [
                { label: 'Máximo', data: data.map(d => d.max_tweets), borderColor: '#94a3b8', borderDash: [5, 5], fill: false },
                { label: 'Promedio', data: data.map(d => d.avg_tweets), borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', fill: true, tension: 0.2 }
            ]
        },
        options: chartOptions
    });
}

function drawPersistence(data) {
    const ctx = document.getElementById('chart-persistence').getContext('2d');
    if (chartInstances.persistence) chartInstances.persistence.destroy();
    const topData = data.slice(0, 15);
    chartInstances.persistence = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topData.map(d => d.trend.length > 20 ? d.trend.substring(0, 20) + '...' : d.trend),
            datasets: [{ label: 'Apariciones', data: topData.map(d => d.appearances), backgroundColor: 'rgba(99, 102, 241, 0.8)', borderRadius: 5 }]
        },
        options: { ...chartOptions, indexAxis: 'y' }
    });
}

function drawSpreadTable(data) {
    const container = document.getElementById('table-spread-body');
    container.innerHTML = '';
    data.forEach(item => {
        const translatedCountries = item.countries.map(c => countryTranslations[c] || c);
        const row = document.createElement('tr');
        row.className = "hover:bg-slate-50 border-b border-slate-100";
        row.innerHTML = `
            <td class="p-4 font-semibold text-blue-600">${item.trend}</td>
            <td class="p-4"><span class="px-2 py-1 rounded text-xs font-bold uppercase ${item.scope === 'global' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'}">${item.scope}</span></td>
            <td class="p-4">${item.in_worldwide ? '🌎 Sí' : 'No'}</td>
            <td class="p-4 text-xs text-slate-500">${translatedCountries.join(', ')}</td>
        `;
        container.appendChild(row);
    });
}

// --- Orquestador de Datos ---
async function refreshData() {
    const range = getUTCRange();
    const pais = document.getElementById('filter-pais').value;
    const granularity = getAutoGranularity(inputFrom.value, inputTo.value);
    const btn = document.getElementById('btn-update');
    
    btn.innerText = 'Cargando...'; btn.disabled = true;

    const params = `?pais=${pais}&date_from=${range.from}&date_to=${range.to}&granularity=${granularity}&limit=50`;

    try {
        const [act, int, per, spr, lastUpd] = await Promise.all([
            fetch(`${API_BASE}/api/metrics/activity${params}`).then(r => r.json()),
            fetch(`${API_BASE}/api/metrics/intensity${params}`).then(r => r.json()),
            fetch(`${API_BASE}/api/metrics/persistence${params}`).then(r => r.json()),
            fetch(`${API_BASE}/api/metrics/spread${params}`).then(r => r.json()),
            fetch(`${API_BASE}/api/last_update`).then(r => r.json())
        ]);

        lastSpreadData = spr.data || [];
        drawActivity(act.data || [], granularity);
        drawIntensity(int.data || []);
        drawPersistence(per.data || []);
        drawSpreadTable(spr.data || []);

        if (lastUpd.last_update) {
            document.getElementById('last-update').innerText = `Último scrapeo detectado: ${formatToLocalTime(lastUpd.last_update)}`;
        }
    } catch (e) {
        console.error("Error al refrescar dashboard:", e);
    } finally {
        btn.innerText = 'Actualizar'; btn.disabled = false;
    }
}

// --- Lógica de la IA (CORREGIDA) ---
document.getElementById('btn-ai').addEventListener('click', async () => {
    const btn = document.getElementById('btn-ai');
    const container = document.getElementById('ai-response-container');
    const textField = document.getElementById('ai-text');
    const nombrePais = document.getElementById('filter-pais').options[document.getElementById('filter-pais').selectedIndex].text;

    if (!lastSpreadData || lastSpreadData.length === 0) {
        alert("Primero carga los datos con el botón 'Actualizar'");
        return;
    }

    btn.disabled = true;
    btn.innerHTML = `⌛ Analizando...`;
    container.classList.remove('hidden');
    textField.innerText = "Generando resumen narrativo con IA...";

    try {
        const response = await fetch(`${API_BASE}/api/ai_summary`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data: lastSpreadData, pais_nombre: nombrePais })
        });

        const result = await response.json();
        textField.innerText = result.summary || "No se recibió respuesta de la IA.";
    } catch (error) {
        textField.innerText = "Error de conexión con la IA.";
    } finally {
        btn.disabled = false;
        btn.innerText = "✨ Generar Análisis";
    }
});

// --- Inicio ---
async function initApp() {
    inputFrom.value = getLocalTodayString();
    inputTo.value = getLocalTodayString();
    refreshData();
}

window.addEventListener('load', initApp);