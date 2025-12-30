/**
 * Twitter Trends Dashboard - Logic & Charts
 */

// Objeto para rastrear las instancias de las gráficas y poder destruirlas antes de recrearlas
const chartInstances = {};

let API_BASE = "";
let lastSpreadData = [];

/**
 * UTILIDADES
 */
const countryTranslations = {
    "worldwide": "Global",
    "united-states": "Estados Unidos",
    "united-kingdom": "Reino Unido",
    "brazil": "Brasil",
    "canada": "Canadá",
    "france": "Francia",
    "germany": "Alemania",
    "india": "India",
    "japan": "Japón",
    "netherlands": "Países Bajos",
    "peru": "Perú",
    "russia": "Rusia",
    "sweden": "Suecia",
    "switzerland": "Suiza",
    "ecuador": "Ecuador",
    "argentina": "Argentina",
    "mexico": "México",
    "colombia": "Colombia",
    "spain": "España",
    "australia": "Australia"
};

// Asegurar coherencia visual en los calendarios
// CORRECCIÓN: Usamos los IDs nuevos (startDate y endDate)
const inputFrom = document.getElementById('startDate');
const inputTo = document.getElementById('endDate');

if (inputFrom && inputTo) {
    inputFrom.addEventListener('change', () => {
        // El "mínimo" de la fecha final ahora es lo que diga la fecha inicial
        inputTo.min = inputFrom.value;
        if (inputTo.value < inputFrom.value) {
            inputTo.value = inputFrom.value;
        }
    });

    inputTo.addEventListener('change', () => {
        // El "máximo" de la fecha inicial ahora es lo que diga la fecha final
        inputFrom.max = inputTo.value;
        if (inputFrom.value > inputTo.value) {
            inputFrom.value = inputTo.value;
        }
    });
}

// Convierte UTC (de MongoDB) a Hora Local del Navegador
function formatToLocalTime(isoString, showTime = true) {
    if (!isoString) return "--:--";
    const date = new Date(isoString);
    
    const options = { 
        day: '2-digit', 
        month: 'short' 
    };

    if (showTime) {
        options.hour = '2-digit';
        options.minute = '2-digit';
    }

    return date.toLocaleString([], options);
}

function getUTCRange() {
    // CORRECCIÓN: IDs actualizados
    const dateFromInput = document.getElementById('startDate').value; 
    const dateToInput = document.getElementById('endDate').value;

    const localFrom = new Date(dateFromInput + "T00:00:00");
    const localTo = new Date(dateToInput + "T23:59:59");

    return {
        from: localFrom.toISOString(),
        to: localTo.toISOString()
    };
}

// Obtiene la fecha actual en formato YYYY-MM-DD respetando la zona horaria local
function getLocalTodayString() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// Decide granularidad basado en el rango de días seleccionados
function getAutoGranularity(dateFrom, dateTo) {
    const start = new Date(dateFrom);
    const end = new Date(dateTo);
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    return diffDays <= 2 ? 'hour' : 'day';
}

// Configuración base para evitar el crecimiento infinito y mejorar estética
const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { position: 'top', labels: { boxWidth: 10, font: { size: 11 } } }
    },
    scales: {
        y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
        x: { grid: { display: false } }
    }
};

/**
 * RENDERS DE GRÁFICAS
 */

function drawActivity(data, granularity) {
    const canvas = document.getElementById('chart-activity');
    if (!canvas) return; // Protección si no existe

    const ctx = canvas.getContext('2d');
    if (chartInstances.activity) chartInstances.activity.destroy();

    const showTime = (granularity === 'hour');

    chartInstances.activity = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => formatToLocalTime(d.timestamp, showTime)),
            datasets: [{
                label: 'Tendencias Activas',
                data: data.map(d => d.total_trends),
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                fill: true,
                tension: 0.3,
                pointRadius: 2
            }]
        },
        options: chartOptions
    });
}

function drawIntensity(data) {
    const canvas = document.getElementById('chart-intensity');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (chartInstances.intensity) chartInstances.intensity.destroy();

    chartInstances.intensity = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.trend),
            datasets: [
                {
                    label: 'Máximo Tweets',
                    data: data.map(d => d.max_tweets),
                    borderColor: '#94a3b8',
                    borderDash: [5, 5],
                    fill: false
                },
                {
                    label: 'Promedio Tweets',
                    data: data.map(d => d.avg_tweets),
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.2
                }
            ]
        },
        options: chartOptions
    });
}

function drawPersistence(data) {
    const canvas = document.getElementById('chart-persistence');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    
    // 1. Destruir instancia previa
    if (chartInstances.persistence) chartInstances.persistence.destroy();

    // 2. Validar que hay datos
    if (!data || data.length === 0) {
        console.warn("No hay datos para Persistencia");
        return;
    }

    // 3. Tomar solo el Top 10 o 15 para que quepa bien en el gráfico
    const topData = data.slice(0, 15);

    chartInstances.persistence = new Chart(ctx, {
        type: 'bar',
        data: {
            // Limpiamos los nombres para que se vean bien
            labels: topData.map(d => d.trend.length > 20 ? d.trend.substring(0, 20) + '...' : d.trend),
            datasets: [{
                label: 'Apariciones (Frecuencia)',
                data: topData.map(d => d.appearances),
                backgroundColor: 'rgba(99, 102, 241, 0.8)',
                borderColor: '#6366f1',
                borderWidth: 1,
                borderRadius: 5,
            }]
        },
        options: {
            indexAxis: 'y', // Barras horizontales
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => ` Apareció ${context.raw} veces`
                    }
                }
            },
            scales: {
                x: { 
                    beginAtZero: true,
                    grid: { display: false }
                },
                y: {
                    ticks: {
                        autoSkip: false, // Forzar que muestre los nombres
                        font: { size: 11 }
                    }
                }
            }
        }
    });
}

function drawSpreadTable(data) {
    const container = document.getElementById('table-spread-body');
    if (!container) return;
    
    container.innerHTML = '';

    data.forEach(item => {
        // Traducimos cada país de la lista
        const translatedCountries = item.countries.map(c => countryTranslations[c] || c);
        
        const row = document.createElement('tr');
        row.className = "hover:bg-slate-50 transition-colors border-b border-slate-100";
        row.innerHTML = `
            <td class="p-4 font-semibold text-blue-600">${item.trend}</td>
            <td class="p-4">
                <span class="px-2 py-1 rounded text-xs font-bold uppercase ${
                    item.scope === 'global' ? 'bg-purple-100 text-purple-700' : 
                    item.scope === 'regional' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600'
                }">${item.scope === 'global' ? 'Global' : item.scope === 'regional' ? 'Regional' : 'Local'}</span>
            </td>
            <td class="p-4">${item.in_worldwide ? '🌎 <span class="text-green-600">Sí</span>' : '<span class="text-slate-400">No</span>'}</td>
            <td class="p-4 text-xs text-slate-500">${translatedCountries.join(', ')}</td>
        `;
        container.appendChild(row);
    });
}
/**
 * ORQUESTADOR DE DATOS
 */

async function refreshData() {
    const range = getUTCRange();
    // CORRECCIÓN: ID actualizado a countrySelect
    const pais = document.getElementById('countrySelect').value;
    const dFrom = document.getElementById('startDate').value;
    const dTo = document.getElementById('endDate').value;
    
    if (new Date(dFrom) > new Date(dTo)) {
        alert("La fecha de inicio ('Desde') no puede ser posterior a la fecha final ('Hasta').");
        document.getElementById('startDate').value = dTo;
        return; 
    }

    const granularity = getAutoGranularity(dFrom, dTo);

    const btn = document.getElementById('btn-update');
    const originalText = btn.innerText;
    btn.innerText = 'Cargando...';
    btn.disabled = true;

    // Nota: Asegúrate de que tu backend tenga rutas como /api/metrics/activity
    const params = `?pais=${pais}&date_from=${range.from}&date_to=${range.to}&granularity=${granularity}&limit=50`;

    try {
        console.log("Fetching from:", API_BASE);
        // Usamos ${API_BASE} antes de cada ruta
        const [act, int, per, spr] = await Promise.all([
            fetch(`${API_BASE}/api/metrics/activity${params}`).then(r => r.json()),
            fetch(`${API_BASE}/api/metrics/intensity${params}`).then(r => r.json()),
            fetch(`${API_BASE}/api/metrics/persistence${params}`).then(r => r.json()),
            fetch(`${API_BASE}/api/metrics/spread${params}`).then(r => r.json())
        ]);

        lastSpreadData = spr.data || [];

        drawActivity(act.data || [], granularity);
        drawIntensity(int.data || []);
        drawPersistence(per.data || []);
        drawSpreadTable(spr.data || []);

        // Actualizar label de "Última actualización" con hora local (si existe el endpoint)
        try {
            const lastUpd = await fetch('/api/last_update').then(r => r.json());
            if (lastUpd && lastUpd.last_update) {
                document.getElementById('last-update').innerText = `Último scrapeo: ${formatToLocalTime(lastUpd.last_update)}`;
            }
        } catch (e) {
            console.log("No se pudo obtener última actualización");
        }

    } catch (e) {
        console.error("Error al refrescar dashboard:", e);
        // alert("Error cargando datos. Revisa la consola.");
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

/**
 * INICIO
 */

// Función para inicializar la aplicación
async function initApp() {
    // Setear fechas por defecto
    const localToday = getLocalTodayString();
    const startEl = document.getElementById('startDate');
    const endEl = document.getElementById('endDate');
    
    if(startEl) startEl.value = localToday;
    if(endEl) endEl.value = localToday;

    try {
        // 1. Obtener la configuración del backend
        const configResp = await fetch('/config');
        if (configResp.ok) {
            const config = await configResp.json();
            API_BASE = config.api_base || "";
        }
        
        console.log("Configuración cargada. API Base:", API_BASE);

        // 2. Cargar datos iniciales
        refreshData();
        
    } catch (error) {
        console.error("Error init:", error);
        refreshData();
    }
}

// Listeners
document.getElementById('btn-update').addEventListener('click', refreshData);

// Resumen Inteligente
document.getElementById('btn-ai').addEventListener('click', async () => {
    const btn = document.getElementById('btn-ai');
    const container = document.getElementById('ai-response-container');
    const textField = document.getElementById('ai-text');
    const paisSelector = document.getElementById('countrySelect');
    const nombrePais = paisSelector.options[paisSelector.selectedIndex].text;

    if (!lastSpreadData || lastSpreadData.length === 0) {
        alert("Primero carga los datos con el botón 'Actualizar'");
        return;
    }

    // UI State
    btn.disabled = true;
    btn.innerHTML = `Analizando...`;
    
    container.classList.remove('hidden');
    textField.innerText = "La IA está examinando las tendencias actuales...";

    try {
        const response = await fetch(`${API_BASE}/api/ai_summary`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                data: lastSpreadData,
                pais_nombre: nombrePais
            })
        });

        const result = await response.json();

        if (response.ok) {
            textField.innerText = result.summary;
        } else {
            textField.innerText = "Error: " + (result.summary || result.error || "No se pudo generar");
        }
    } catch (error) {
        console.error("Error en AI:", error);
        textField.innerText = "Error de conexión con el servidor.";
    } finally {
        btn.disabled = false;
        btn.innerText = "✨ Generar Análisis";
    }
});

// Arrancar
window.addEventListener('load', initApp);