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
const inputFrom = document.getElementById('filter-date-from');
const inputTo = document.getElementById('filter-date-to');

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

// Convierte UTC (de MongoDB) a Hora Local del Navegador
function formatToLocalTime(isoString, showTime = true) {
    if (!isoString) return "--:--";

    let normalizedString = isoString;
    if (isoString.match(/\d{4}-\d{2}-\d{2}-\d{2}$/)) {
        normalizedString = isoString.replace(/-(\d{2})$/, 'T$1:00:00');
    }

    const date = new Date(normalizedString);
    
    // Si sigue siendo inválida, mostramos el string original para no romper la UI
    if (isNaN(date.getTime())) return isoString;

    const options = { 
        day: '2-digit', 
        month: 'short' 
    };

    if (showTime) {
        options.hour = '2-digit',
        options.minute = '2-digit',
        options.hour12 = false
    }

    return date.toLocaleString([], options);
}

function getUTCRange() {
    const dateFromInput = document.getElementById('filter-date-from').value; //
    const dateToInput = document.getElementById('filter-date-to').value;

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
    const ctx = document.getElementById('chart-activity').getContext('2d');
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
    const ctx = document.getElementById('chart-intensity').getContext('2d');
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
    const ctx = document.getElementById('chart-persistence').getContext('2d');
    
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
    const pais = document.getElementById('filter-pais').value;
    const dFrom = document.getElementById('filter-date-from').value;
    const dTo = document.getElementById('filter-date-to').value;
    if (new Date(dFrom) > new Date(dTo)) {
        alert("La fecha de inicio ('Desde') no puede ser posterior a la fecha final ('Hasta').");
        document.getElementById('filter-date-from').value = dTo;
        return; 
    }

    const granularity = getAutoGranularity(dFrom, dTo);

    const btn = document.getElementById('btn-update');
    btn.innerText = 'Cargando...';
    btn.disabled = true;

    const params = `?pais=${pais}&date_from=${range.from}&date_to=${range.to}&granularity=${granularity}&limit=50`;

    try {
        // Usamos ${API_BASE} antes de cada ruta
        const [act, int, per, spr] = await Promise.all([
            fetch(`${API_BASE}/api/metrics/activity${params}`).then(r => r.json()),
            fetch(`${API_BASE}/api/metrics/intensity${params}`).then(r => r.json()),
            fetch(`${API_BASE}/api/metrics/persistence${params}`).then(r => r.json()),
            fetch(`${API_BASE}/api/metrics/spread${params}`).then(r => r.json())
        ]);

        lastSpreadData = spr.data;

        drawActivity(act.data, granularity);
        drawIntensity(int.data);
        drawPersistence(per.data);
        drawSpreadTable(spr.data);

        // Actualizar label de "Última actualización" con hora local
        const lastUpd = await fetch('/api/last_update').then(r => r.json());
        document.getElementById('last-update').innerText = `Último scrapeo detectado: ${formatToLocalTime(lastUpd.last_update)}`;

    } catch (e) {
        console.error("Error al refrescar dashboard:", e);
    } finally {
        btn.innerText = 'Actualizar';
        btn.disabled = false;
    }
}

/**
 * INICIO
 */

// Setear fechas por defecto usando la función de fecha local
const localToday = getLocalTodayString();
document.getElementById('filter-date-from').value = localToday;
document.getElementById('filter-date-to').value = localToday;

// Listeners
document.getElementById('btn-update').addEventListener('click', refreshData);

// Resumen Inteligente
document.getElementById('btn-ai').addEventListener('click', async () => {
    const btn = document.getElementById('btn-ai');
    const container = document.getElementById('ai-response-container');
    const textField = document.getElementById('ai-text');
    const paisSelector = document.getElementById('filter-pais');
    const nombrePais = paisSelector.options[paisSelector.selectedIndex].text;

    if (!lastSpreadData || lastSpreadData.length === 0) {
        alert("Primero carga los datos con el botón 'Actualizar'");
        return;
    }

    // UI State
    btn.disabled = true;
    btn.innerHTML = `
        <svg class="animate-spin h-4 w-4 text-white inline mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
        Analizando...
    `;
    
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

// Función para inicializar la aplicación
async function initApp() {
    try {
        // 1. Obtener la configuración del backend
        const configResp = await fetch('/api/config');
        const config = await configResp.json();
        
        // 2. Guardar la URL base
        API_BASE = config.api_base;
        console.log("Configuración cargada. API Base:", API_BASE);

        // 3. Ahora que tenemos la IP, cargamos los datos por primera vez
        refreshData();
        
    } catch (error) {
        console.error("Error al cargar la configuración inicial:", error);
        // Fallback por si acaso falla el endpoint
        API_BASE = window.location.origin; 
        refreshData();
    }
}

// Cambiamos el window.onload por nuestra nueva función initApp
window.addEventListener('load', initApp);