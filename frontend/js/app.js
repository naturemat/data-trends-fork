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
// 1. Forzar visualización en UTC
function formatToLocalTime(isoString, showTime = true) {
    if (!isoString) return "--:--";
    
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return isoString;

    const options = { 
        day: '2-digit', 
        month: 'short'
    };

    if (showTime) {
        options.hour = '2-digit';
        options.minute = '2-digit';
        options.hour12 = false;
    }

    return date.toLocaleDateString('es-ES', options);
}

function getLocalTodayString() {
    const now = new Date();
    const offset = now.getTimezoneOffset() * 60000;
    const localISOTime = (new Date(now - offset)).toISOString().split('T')[0];
    return localISOTime;
}

function getUTCRange() {
    const dFrom = document.getElementById('filter-date-from').value; 
    const dTo = document.getElementById('filter-date-to').value;

    return {
        from: `${dFrom}T00:00:00`,
        to: `${dTo}T23:59:59`
    };
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
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    if (chartInstances.activity) chartInstances.activity.destroy();

    const showTime = (granularity === 'hour');
    
    // CAMBIO: Ahora usamos 'new_trends' para el máximo y los datos
    const maxValue = Math.max(...data.map(d => d.new_trends), 0);
    // Ajuste dinámico del eje Y: si hay pocas nuevas, el techo es 10, si hay muchas, sube de 10 en 10
    const yMax = maxValue > 10 ? Math.ceil((maxValue + 1) / 10) * 10 : 10;

    chartInstances.activity = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => formatToLocalTime(d.timestamp, showTime)),
            datasets: [{
                label: 'Nuevas Tendencias',
                data: data.map(d => d.new_trends), // CAMBIO AQUÍ
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: '#ffffff',
                pointBorderWidth: 2,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: yMax, 
                    ticks: {
                        stepSize: 10,
                        precision: 0
                    },
                    grid: { color: '#f1f5f9' }
                },
                x: {
                    ticks: { font: { size: 10 }, maxRotation: 45 },
                    grid: { display: false }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1e293b',
                    padding: 12,
                    callbacks: {
                        title: (items) => `📅 ${items[0].label}`,
                        label: (item) => ` Temas nuevos: ${item.raw}` // CAMBIO AQUÍ
                    }
                }
            }
        }
    });
}

function drawSurvival(data) {
    const canvas = document.getElementById('chart-impact');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    if (chartInstances.survival) chartInstances.survival.destroy();

    chartInstances.survival = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.label),
            datasets: [{
                data: data.map(d => d.count),
                backgroundColor: [
                    '#ef4444', // Rojo (Fugaz)
                    '#f59e0b', // Naranja (Activa)
                    '#3b82f6', // Azul (Persistente)
                    '#10b981'  // Verde (Inmortal)
                ],
                borderRadius: 6,
                barThickness: 40
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1e293b',
                    padding: 12
                }
            },
            scales: {
                y: { 
                    beginAtZero: true, 
                    ticks: { precision: 0 },
                    grid: { color: '#f1f5f9' }
                },
                x: { grid: { display: false } }
            }
        }
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
    if (!container) return; 
    container.innerHTML = '';

    data.forEach(item => {
        const translatedCountries = item.countries.map(c => countryTranslations[c] || c);
        
        const scopeKey = item.scope.toLowerCase(); 
        const badgeClass = `badge-${scopeKey}`;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="p-4 font-semibold text-blue-600">${item.trend}</td>
            <td class="p-4">
                <span class="badge ${badgeClass}">
                    ${item.scope === 'global' ? 'Global' : item.scope === 'regional' ? 'Regional' : 'Local'}
                </span>
            </td>
            <td class="p-4 text-xl">
                ${item.in_worldwide ? '✅' : '❌'}
            </td>
            <td class="p-4 text-xs text-slate-500 font-medium">${translatedCountries.join(', ')}</td>
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
    
    // Validación de rango
    if (new Date(dFrom) > new Date(dTo)) {
        alert("La fecha de inicio no puede ser posterior a la fecha final.");
        return; 
    }

    const granularity = getAutoGranularity(dFrom, dTo);
    const btn = document.getElementById('btn-update');
    btn.innerText = 'Cargando...';
    btn.disabled = true;

    // Dentro de refreshData, la línea de params queda así:
const params = `?pais=${pais}&date_from=${range.from}&date_to=${range.to}&granularity=${granularity}&limit=50`;

    try {
        const [act, per, spr, lastUpd, summary, surv] = await Promise.all([
            fetch(`${API_BASE}/api/metrics/activity${params}`).then(r => r.json()),
            fetch(`${API_BASE}/api/metrics/persistence${params}`).then(r => r.json()),
            fetch(`${API_BASE}/api/metrics/spread${params}`).then(r => r.json()),
            fetch(`${API_BASE}/api/last_update`).then(r => r.json()),
            fetch(`${API_BASE}/api/metrics/summary${params}`).then(r => r.json()),
            fetch(`${API_BASE}/api/metrics/survival${params}`).then(r => r.json())
        ]);

        lastSpreadData = spr.data || [];

        drawActivity(act.data || [], granularity);
        drawPersistence(per.data || []);
        drawSpreadTable(spr.data || []);
        drawSurvival(surv.data || []);

        // Actualizar label de "Última actualización"
        if (lastUpd.last_update) {
            document.getElementById('last-update').innerText = 
                `Último scrapeo detectado: ${formatToLocalTime(lastUpd.last_update)}`;
        }

        // Actualización de Cards con datos del Summary
        const total = summary.total_unique || 0;
        const globales = summary.total_global || 0;
        const pct = total > 0 ? ((globales / total) * 100).toFixed(1) : 0;

        document.getElementById('stat-total').innerText = total;
        document.getElementById('stat-paises').innerText = summary.total_paises || 1;
        document.getElementById('stat-globales').innerText = globales;
        document.getElementById('stat-globales-pct').innerText = `(${pct}%)`;

        loadTopicStructure();
        
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

/**
 * RENDER DE ESTRUCTURA TEMÁTICA (Embeddings)
 */
async function loadTopicStructure() {
    const container = document.getElementById('topic-cards-container');
    if (!container) return;

    try {
        const response = await fetch(`${API_BASE}/api/embeddings/enrich`);
        const data = await response.json();
        const trends = data.trends || [];

        if (trends.length === 0) {
            container.innerHTML = `<p class="col-span-full text-center text-slate-400 italic">No hay datos de enriquecimiento disponibles.</p>`;
            return;
        }

        // 1. Agrupar tendencias por tópico
        const grouped = trends.reduce((acc, item) => {
            const topic = item.topic || 'Otros';
            if (!acc[topic]) acc[topic] = [];
            acc[topic].push(item.trend_text);
            return acc;
        }, {});

        // 2. Convertir a array y ordenar por volumen (Top 5)
        const sortedTopics = Object.entries(grouped)
            .sort((a, b) => b[1].length - a[1].length)
            .slice(0, 6); // Tomamos 6 para que el grid se vea lleno

        container.innerHTML = ''; // Limpiar estado de carga

        // 3. Renderizar cada tarjeta
        sortedTopics.forEach(([topicName, items]) => {
            // Formatear nombre: "business_&_finance" -> "Business & Finance"
            const cleanName = topicName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            
            const card = document.createElement('div');
            card.className = "bg-white rounded-2xl p-5 border border-slate-100 shadow-sm hover:shadow-md transition-shadow flex flex-col gap-4";
            
            card.innerHTML = `
                <div class="flex justify-between items-start">
                    <span class="px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-[10px] font-black uppercase tracking-wider">
                        ${cleanName}
                    </span>
                    <span class="text-[10px] font-bold text-slate-400 bg-slate-50 px-2 py-1 rounded-md">
                        ${items.length} temas
                    </span>
                </div>
                <div class="flex flex-wrap gap-1.5">
                    ${items.slice(0, 10).map(t => `
                        <span class="text-[10px] bg-slate-50 text-slate-600 px-2 py-1 rounded border border-slate-100 italic">
                            ${t}
                        </span>
                    `).join('')}
                    ${items.length > 10 ? `<span class="text-[10px] text-slate-400 self-center">...</span>` : ''}
                </div>
            `;
            container.appendChild(card);
        });

    } catch (e) {
        console.error("Error cargando tópicos:", e);
        container.innerHTML = `<p class="col-span-full text-center text-red-400">Error al conectar con el motor de embeddings.</p>`;
    }
}

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
// Función para inicializar la aplicación
async function initApp() {
    try {
        const configResp = await fetch('/api/config');
        const config = await configResp.json();
        
        API_BASE = window.location.origin; 
        
        console.log("Configuración cargada. Usando API Base relativa:", API_BASE);

        refreshData();
        
    } catch (error) {
        console.error("Error al cargar la configuración inicial:", error);
        API_BASE = window.location.origin; 
        refreshData();
    }
}

window.addEventListener('load', initApp);