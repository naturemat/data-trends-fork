/**
 * Twitter Trends Dashboard - Main Logic (Versión Pro)
 * Conectado al Backend Python robusto (/api/metrics/...)
 */

const chartInstances = {};
let API_BASE = ""; // Usamos ruta relativa, Nginx maneja el resto.

// --- CONFIGURACIÓN DE FECHAS ---
const inputFrom = document.getElementById('startDate');
const inputTo = document.getElementById('endDate');

if (inputFrom && inputTo) {
    inputFrom.addEventListener('change', () => {
        inputTo.min = inputFrom.value;
        if (inputTo.value < inputFrom.value) inputTo.value = inputFrom.value;
    });
    inputTo.addEventListener('change', () => {
        inputFrom.max = inputTo.value;
        if (inputFrom.value > inputTo.value) inputFrom.value = inputTo.value;
    });
}

// --- UTILIDADES ---
function getLocalTodayString() {
    const now = new Date();
    return now.toISOString().split('T')[0];
}

function formatToLocalTime(isoString) {
    if (!isoString) return "--:--";
    const date = new Date(isoString);
    return date.toLocaleString([], { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
}

// --- GRÁFICAS ---
const chartOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { position: 'top', labels: { boxWidth: 10, font: { size: 11 } } } },
    scales: { y: { beginAtZero: true }, x: { grid: { display: false } } }
};

function drawActivity(data) {
    const ctx = document.getElementById('chart-activity')?.getContext('2d');
    if (!ctx) return;
    if (chartInstances.activity) chartInstances.activity.destroy();

    // Adaptamos según si viene 'data' anidado o directo
    const points = Array.isArray(data) ? data : (data.data || []);

    chartInstances.activity = new Chart(ctx, {
        type: 'line',
        data: {
            labels: points.map(d => formatToLocalTime(d.timestamp)),
            datasets: [{
                label: 'Tendencias Activas',
                data: points.map(d => d.total_trends),
                borderColor: '#2563eb', backgroundColor: 'rgba(37, 99, 235, 0.1)', fill: true, tension: 0.3
            }]
        }, options: chartOptions
    });
}

function drawIntensity(data) {
    const ctx = document.getElementById('chart-intensity')?.getContext('2d');
    if (!ctx) return;
    if (chartInstances.intensity) chartInstances.intensity.destroy();

    const points = Array.isArray(data) ? data : (data.data || []);

    chartInstances.intensity = new Chart(ctx, {
        type: 'line',
        data: {
            labels: points.map(d => d.trend),
            datasets: [
                { label: 'Máximo', data: points.map(d => d.max_tweets), borderColor: '#94a3b8', borderDash: [5, 5], fill: false },
                { label: 'Promedio', data: points.map(d => d.avg_tweets), borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', fill: true }
            ]
        }, options: chartOptions
    });
}

function drawPersistence(data) {
    const ctx = document.getElementById('chart-persistence')?.getContext('2d');
    if (!ctx) return;
    if (chartInstances.persistence) chartInstances.persistence.destroy();

    const points = Array.isArray(data) ? data : (data.data || []);
    const topData = points.slice(0, 15);

    chartInstances.persistence = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topData.map(d => d.trend),
            datasets: [{
                label: 'Apariciones', data: topData.map(d => d.appearances),
                backgroundColor: 'rgba(99, 102, 241, 0.8)', borderColor: '#6366f1', borderWidth: 1, indexAxis: 'y'
            }]
        }, options: { ...chartOptions, indexAxis: 'y' }
    });
}

function drawSpreadTable(data) {
    const container = document.getElementById('table-spread-body');
    if (!container) return;
    container.innerHTML = '';
    
    const points = Array.isArray(data) ? data : (data.data || []);

    points.forEach(item => {
        // Validación de seguridad por si faltan campos
        const trendName = item.trend || "Desconocido";
        const scope = item.scope || "local";
        const countries = Array.isArray(item.countries) ? item.countries.join(', ') : "N/A";

        container.innerHTML += `
            <tr class="hover:bg-slate-50 border-b border-slate-100">
                <td class="p-4 font-semibold text-blue-600">${trendName}</td>
                <td class="p-4"><span class="px-2 py-1 rounded text-xs font-bold uppercase bg-slate-100 text-slate-600">${scope}</span></td>
                <td class="p-4 text-xs text-slate-500">${countries}</td>
            </tr>`;
    });
}

// --- ORQUESTADOR ---
async function refreshData() {
    const btn = document.getElementById('btn-update');
    const originalText = btn.innerText;
    btn.innerText = 'Cargando...'; btn.disabled = true;

    try {
        const countrySelect = document.getElementById('countrySelect') || document.getElementById('filter-pais');
        const pais = countrySelect ? countrySelect.value : 'worldwide';
        const start = document.getElementById('startDate').value;
        const end = document.getElementById('endDate').value;
        
        // Parámetros comunes
        const params = `?pais=${pais}&date_from=${start}&date_to=${end}&granularity=hour&limit=50`;
        
        console.log("Fetching endpoints...");

        // Llamadas paralelas a los endpoints REALES que tienes en routes.py
        const [act, int, per, spr] = await Promise.all([
            fetch(`${API_BASE}/api/metrics/activity${params}`).then(r => r.json()),
            fetch(`${API_BASE}/api/metrics/intensity${params}`).then(r => r.json()),
            fetch(`${API_BASE}/api/metrics/persistence${params}`).then(r => r.json()),
            fetch(`${API_BASE}/api/metrics/spread${params}`).then(r => r.json())
        ]);

        drawActivity(act);
        drawIntensity(int);
        drawPersistence(per);
        drawSpreadTable(spr);

        // Actualizar última hora
        const lastUpd = await fetch(`${API_BASE}/api/last_update`).then(r => r.json()).catch(() => null);
        if (lastUpd && lastUpd.last_update) {
            document.getElementById('last-update').innerText = `Último scrapeo: ${formatToLocalTime(lastUpd.last_update)}`;
        }

    } catch (e) {
        console.error("Error obteniendo datos:", e);
    } finally {
        btn.innerText = originalText; btn.disabled = false;
    }
}

// --- INICIO ---
window.addEventListener('load', () => {
    const today = getLocalTodayString();
    if(inputFrom) inputFrom.value = today;
    if(inputTo) inputTo.value = today;
    
    const btnUpdate = document.getElementById('btn-update');
    if(btnUpdate) btnUpdate.addEventListener('click', refreshData);
    
    // IA Button
    const btnAi = document.getElementById('btn-ai');
    if(btnAi) btnAi.addEventListener('click', async () => {
         alert("IA: Conectando...");
         // Aquí puedes reactivar la lógica de IA si la necesitas
    });

    console.log("App iniciada. Modo Pro.");
    refreshData();
});