/**
 * Twitter Trends Dashboard - Logic & Charts
 */

// Objeto para rastrear las instancias de las gráficas y poder destruirlas antes de recrearlas
const chartInstances = {};

let API_BASE = "";
let lastPersistenceData = [];
let chartAiCategories = null;

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
        legend: { position: 'top', labels: { boxWidth: 10, font: {family: "'Montserrat', sans-serif", size: 11 } } }
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
                    ticks: { font: {family: "'Montserrat', sans-serif", size: 10 }, maxRotation: 45 },
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

    const aiColors = ['#BFDBFE', '#60A5FA', '#2563EB', '#1E3A8A'];

    chartInstances.survival = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.label),
            datasets: [{
                label: 'Cantidad de Tendencias',
                data: data.map(d => d.count),
                backgroundColor: aiColors.map(color => color + 'dd'),
                borderColor: aiColors,
                borderWidth: 2,
                borderRadius: 8,
                hoverBackgroundColor: aiColors,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    callbacks: {
                        label: (context) => ` Total: ${context.raw} tendencias`,
                        afterBody: function(context) {
                            const index = context[0].dataIndex;
                            const trends = data[index].topTrends || [];
                            if (trends.length === 0) return '';
                            let text = ['\nTop 3 temas:'];
                            trends.slice(0, 3).forEach((t, i) => {
                                text.push(`${i + 1}. ${t}`);
                            });
                            return text;
                        }
                    }
                }
            },
            scales: {
                y: { 
                    type: 'logarithmic',
                    beginAtZero: false,
                    min: 0.1,
                    ticks: {
                        callback: function(value) {
                            // Esto limpia los ticks para que solo se vean números enteros (1, 10, 100, 1000...)
                            if (value === 1 || value === 10 || value === 100 || value === 1000 || value === 5000) {
                                return value;
                            }
                        },
                        font: { family: "'Montserrat', sans-serif", weight: '600' }
                    },
                    grid: { color: '#f1f5f9' }
                },
                x: { 
                    grid: { display: false },
                    ticks: { font: { family: "'Montserrat', sans-serif", weight: '700' } }
                }
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
                        font: {family: "'Montserrat', sans-serif", size: 11 }
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
            <td class="p-4 text-xl text-center align-middle">
                ${item.in_worldwide ? `<i data-lucide="check-circle"></i>`
            : `<i data-lucide="x-circle"></i>`}
            </td>
            <td class="p-4 text-xs text-slate-500 font-medium">${translatedCountries.join(', ')}</td>
        `;
        container.appendChild(row);
    });
    lucide.createIcons();
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

        lastPersistenceData = per.data || [];

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
        
        // Limpiar la sección de IA al actualizar filtros
        const topicContainer = document.getElementById('topic-cards-container');
        if (topicContainer) {
            topicContainer.innerHTML = `
                <div class="col-span-full py-10 text-center bg-white rounded-2xl border-2 border-dashed border-slate-200">
                    <p class="text-slate-400 font-medium italic">Datos actualizados. Presiona el botón superior para clasificar...</p>
                </div>`;
        }
        document.getElementById('ai-response-container').classList.add('hidden');

        if (chartInstances.aiCategories) {
            chartInstances.aiCategories.destroy();
            chartInstances.aiCategories = null; // Liberar memoria
            
            // Opcional: Limpiar el canvas visualmente para que no quede el último frame
            const aiCanvas = document.getElementById('chart-ai-categories');
            if (aiCanvas) {
                const ctx = aiCanvas.getContext('2d');
                ctx.clearRect(0, 0, aiCanvas.width, aiCanvas.height);
            }
        }

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
    const paisCodigo = document.getElementById('filter-pais').value;
    
    // Obtenemos el nombre legible del país (ej: "Ecuador" en lugar de "ecuador")
    const paisNombre = countryTranslations[paisCodigo] || paisCodigo;
    
    const range = getUTCRange();
    const params = `?pais=${paisCodigo}&date_from=${range.from}&date_to=${range.to}`;

    // Validamos la nueva variable
    if (!lastPersistenceData || lastPersistenceData.length === 0) {
        alert("Primero carga los datos con el botón 'Actualizar'");
        return;
    }

    btn.disabled = true;
    btn.innerHTML = `⏳ Analizando persistencia...`;
    container.classList.remove('hidden');
    textField.innerText = "La IA está examinando los temas más estables en el tiempo...";

    try {
        const [resSummary, resClass] = await Promise.all([
            fetch(`${API_BASE}/api/ai_summary`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                // ENVIAMOS PERSISTENCIA Y NOMBRE BONITO
                body: JSON.stringify({ 
                    data: lastPersistenceData, 
                    pais_nombre: paisNombre 
                })
            }).then(r => r.json()),
            fetch(`${API_BASE}/api/metrics/ai_classification${params}`).then(r => r.json())
        ]);

        textField.innerText = resSummary.summary || "No se pudo generar el resumen.";

        if (resClass && !resClass.error) {
            renderAiClassification(resClass);
        }

    } catch (error) {
        console.error("Error en el motor de IA:", error);
        textField.innerText = "Error de conexión con los servicios de IA.";
    } finally {
        btn.disabled = false;
        btn.innerText = "✨ Generar Análisis";
    }
});

function renderAiClassification(data) {
    const container = document.getElementById('topic-cards-container');
    const canvas = document.getElementById('chart-ai-categories');
    if (!container || !canvas) return;

    container.innerHTML = ''; // Limpiar mensaje de espera
    
    // 1. Convertir el objeto en una lista y ORDENAR por cantidad de tendencias (descendente)
    const sortedCategories = Object.entries(data)
        .filter(([_, trends]) => trends.length > 0) // Solo categorías con datos
        .sort((a, b) => b[1].length - a[1].length); // Ordenar: mayor a menor

    const labels = [];
    const counts = [];
    // Paleta de colores consistente
    const colors = ['#6366f1', '#ec4899', '#f59e0b', '#10b981', '#3b82f6', '#94a3b8'];

    // 2. Iterar sobre los datos YA ORDENADOS
    sortedCategories.forEach(([category, trends], index) => {
        labels.push(category);
        counts.push(trends.length);

        const currentColor = colors[index % colors.length];

        // Crear Tarjeta con el color sincronizado
        const card = document.createElement('div');
        card.className = "bg-white rounded-2xl p-5 border border-slate-100 shadow-sm hover:shadow-md transition-all flex flex-col gap-4 border-t-4";
        card.style.borderTopColor = currentColor; // Sincronización con el gráfico
        
        card.innerHTML = `
            <div class="flex justify-between items-start">
                <span class="font-black text-xs uppercase tracking-widest text-slate-800">${category}</span>
                <span class="text-[11px] font-bold px-2 py-0.5 rounded-full" 
                      style="background-color: ${currentColor}20; color: ${currentColor}">
                    ${trends.length} temas
                </span>
            </div>
            <div class="flex flex-wrap gap-2 max-h-[200px] overflow-y-auto pr-2 custom-scrollbar">
                ${trends.map(t => `
                    <span class="text-[12px] sm:text-[13px] bg-slate-50 text-slate-700 px-3 py-1.5 rounded-lg border border-slate-200 font-semibold shadow-sm hover:bg-white transition-colors">
                        ${t}
                    </span>
                `).join('')}
            </div>
        `;
        container.appendChild(card);
    });

    // 3. Dibujar Gráfico (ya recibirá las etiquetas y conteos ordenados)
    if (chartInstances.aiCategories) chartInstances.aiCategories.destroy();
    
    chartInstances.aiCategories = new Chart(canvas.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: colors.slice(0, labels.length), // Usar solo los colores necesarios
                borderWidth: 0,
                hoverOffset: 15
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    position: 'bottom', 
                    labels: { 
                        boxWidth: 12, 
                        padding: 15,
                        font: { size: 10, weight: 'bold', family: "'Montserrat', sans-serif",} 
                    } 
                }
            },
            cutout: '70%',
            animation: {
                animateScale: true,
                animateRotate: true
            }
        }
    });
}

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