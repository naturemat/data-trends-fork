// =======================================
// main.js - Dashboard de Tendencias
// =======================================

let allData = [];
let trendsChart = null;
let countryChart = null;

let startDate = null;
let endDate = null;
let startTime = null;
let endTime = null;

let aiModal;
let aiSummary;
let closeModal;

const countryMap = {
    worldwide: "Global",
    australia: "Australia",
    brazil: "Brasil",
    canada: "Canadá",
    france: "Francia",
    germany: "Alemania",
    india: "India",
    japan: "Japón",
    netherlands: "Países Bajos",
    peru: "Perú",
    russia: "Rusia",
    sweden: "Suecia",
    switzerland: "Suiza",
    ecuador: "Ecuador",
    argentina: "Argentina",
    mexico: "México",
    colombia: "Colombia",
    spain: "España",
    "united-kingdom": "Reino Unido",
    "united-states": "Estados Unidos"
};

// URL base de la API (ajusta según si es local o EC2)
const API_BASE = "http://127.0.0.1:5000";

document.addEventListener("DOMContentLoaded", () => {
    const now = new Date();

    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const dd = String(now.getDate()).padStart(2, '0');
    const hh = String(now.getHours()).padStart(2, '0');
    const min = String(now.getMinutes()).padStart(2, '0');

    const defaultStartDate = `${yyyy}-${mm}-${dd}`;
    const defaultEndDate = `${yyyy}-${mm}-${dd}`;
    const defaultStartTime = "00:00";
    const defaultEndTime = `${hh}:${min}`;

    document.getElementById("startDate").value = defaultStartDate;
    document.getElementById("endDate").value = defaultEndDate;
    document.getElementById("startTime").value = defaultStartTime;
    document.getElementById("endTime").value = defaultEndTime;

    startDate = defaultStartDate;
    endDate = defaultEndDate;
    startTime = defaultStartTime;
    endTime = defaultEndTime;

    loadData();

    document.getElementById("countrySelect").addEventListener("change", updateDashboard);
    document.getElementById("topSelect").addEventListener("change", updateDashboard);
    document.getElementById("compareBtn").addEventListener("click", compareCountries);

    document.getElementById("applyDateFilter").addEventListener("click", () => {
        const newStartDate = document.getElementById("startDate").value;
        const newEndDate = document.getElementById("endDate").value;
        const newStartTime = document.getElementById("startTime").value;
        const newEndTime = document.getElementById("endTime").value;

        if (!validateDateTimeFilters(newStartDate, newStartTime, newEndDate, newEndTime)) return;

        startDate = newStartDate || startDate;
        endDate = newEndDate || endDate;
        startTime = newStartTime || startTime;
        endTime = newEndTime || endTime;

        updateDashboard();
        showToast("Filtros aplicados");
    });


    document.getElementById("clearFilters").addEventListener("click", () => {
        startDate = defaultStartDate;
        endDate = defaultEndDate;
        startTime = defaultStartTime;
        endTime = defaultEndTime;

        document.getElementById("startDate").value = startDate;
        document.getElementById("endDate").value = endDate;
        document.getElementById("startTime").value = startTime;
        document.getElementById("endTime").value = endTime;

        updateDashboard();
        showToast("Filtros eliminados");
    });

    aiModal = document.getElementById("aiModal");
    aiSummary = document.getElementById("aiSummary");
    closeModal = document.getElementById("closeModal");

    closeModal.addEventListener("click", () => {
        aiModal.classList.add("hidden");
    });

    aiModal.addEventListener("click", (e) => {
        if (e.target === aiModal) {
            aiModal.classList.add("hidden");
        }
    });

    document.getElementById("analyzeBtn").addEventListener("click", async () => {
        const filteredData = getFilteredDataForAI();

        if (!filteredData.length) {
            showToast("No hay datos filtrados para analizar");
            return;
        }

        aiSummary.textContent = "🤖 Analizando tendencias...";
        aiModal.classList.remove("hidden");

        try {
            const res = await fetch(`${API_BASE}/ai_summary`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ data: filteredData })
            });

            const result = await res.json();
            aiSummary.textContent = result.summary || "No se pudo generar el resumen";

        } catch (err) {
            console.error(err);
            aiSummary.textContent = "Error generando resumen con IA";
        }
    });

    setupTabs();
});



// =======================================
// CARGA DE DATOS DESDE API
// =======================================
async function loadData() {
    try {
        const response = await fetch(`${API_BASE}/trends`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        allData = await response.json();

        // Adaptar datos al formato esperado
        allData = allData.map(d => ({
            fecha: d.fecha || "2025-01-01",
            hora: d.hora || "00:00",
            trend: d.trend || d.tendencia || "",
            tweet_count: d.tweet_count || d.numeroDeTwits || 0,
            country: (d.country || d.pais || "").toLowerCase()
        }));

        populateCountrySelector();
        updateDashboard();
        showLastUpdate();

    } catch (err) {
        console.error("Error cargando tendencias:", err);
        showToast("❌ Error cargando tendencias desde el servidor");
    }
}

// =======================================
// UTILIDADES
// =======================================
function translateCountry(code) { return countryMap[code] || code; }
function formatNumber(num) { return num.toLocaleString("es-ES"); }

async function showLastUpdate() {
    try {
        const res = await fetch(`${API_BASE}/last_update`);
        const data = await res.json();
        document.getElementById("lastUpdate").textContent = `Última actualización: ${data.last_update}`;
    } catch (err) {
        console.error("Error obteniendo última actualización:", err);
    }
}

// =======================================
// FILTROS
// =======================================
function filterByDateTime(data) {
    const sDateTime = startDate ? new Date(startDate + "T" + (startTime || "00:00")) : null;
    const eDateTime = endDate ? new Date(endDate + "T" + (endTime || "23:59")) : null;

    return data.filter(d => {
        const dt = new Date(d.fecha + "T" + d.hora);
        if (sDateTime && dt < sDateTime) return false;
        if (eDateTime && dt > eDateTime) return false;
        return true;
    });
}

// =======================================
// AGRUPAR TENDENCIAS (último registro por día y país)
// =======================================
function groupByTrend(data) {
    const grouped = {};
    data.forEach(d => {
        // clave única por tendencia + país + fecha
        const key = d.trend + '||' + d.country + '||' + d.fecha;

        // si no existe, o si este registro es más reciente, lo guardamos
        if (!grouped[key] || new Date(d.fecha + "T" + d.hora) > new Date(grouped[key].fecha + "T" + grouped[key].hora)) {
            grouped[key] = { ...d };
        }
    });

    // ahora sumamos por tendencia + país (manteniendo solo el último por día)
    const finalGroup = {};
    Object.values(grouped).forEach(d => {
        const key = d.trend + '||' + d.country;
        if (!finalGroup[key]) finalGroup[key] = { ...d };
        else finalGroup[key].tweet_count += d.tweet_count;
    });

    return Object.values(finalGroup);
}

// =======================================
// SELECTORES
// =======================================
function populateCountrySelector() {
    const select = document.getElementById("countrySelect");
    const c1 = document.getElementById("country1");
    const c2 = document.getElementById("country2");

    select.innerHTML = `<option value="all">Todos</option>`;
    c1.innerHTML = "";
    c2.innerHTML = "";

    [...new Set(allData.map(d => d.country))].forEach(c => {
        const label = translateCountry(c);
        select.appendChild(new Option(label, c));
        c1.appendChild(new Option(label, c));
        c2.appendChild(new Option(label, c));
    });
}

// =======================================
// DASHBOARD Y GRÁFICOS
// =======================================
function updateDashboard() {
    const country = document.getElementById("countrySelect").value;
    const topN = parseInt(document.getElementById("topSelect").value);

    let data = filterByDateTime([...allData]);
    if (country !== "all") data = data.filter(d => d.country === country);

    data = groupByTrend(data);
    data.sort((a, b) => b.tweet_count - a.tweet_count);

    updateTrendsChart(data.slice(0, topN));
    updateCountryChart(data);
    updateGlobalStats();
    compareCountries();
}

function updateTrendsChart(data) {
    if (trendsChart) trendsChart.destroy();
    trendsChart = new Chart(document.getElementById("trendsChart"), {
        type: "bar",
        data: {
            labels: data.map(d => `${d.trend} (${translateCountry(d.country)})`),
            datasets: [{ data: data.map(d => d.tweet_count), backgroundColor: "#2563eb" }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { 
                y: { ticks: { callback: value => formatNumber(value) } },
                x: {
                    ticks: {
                        autoSkip: false,  // mostrar todos
                        maxRotation: 45,  // rotar hasta 45 grados
                        minRotation: 30
                    }
                }
            }
        }
    });
}


function updateCountryChart(dataFiltered) {
    if (countryChart) countryChart.destroy();
    const totals = {};
    const data = dataFiltered || filterByDateTime([...allData]);
    const grouped = groupByTrend(data);
    grouped.forEach(d => totals[d.country] = (totals[d.country] || 0) + d.tweet_count);

    const sorted = Object.entries(totals).sort((a,b)=>b[1]-a[1]);
    countryChart = new Chart(document.getElementById("countryChart"), {
        type: "pie",
        data: { 
            labels: sorted.map(d => translateCountry(d[0])), 
            datasets: [{ 
                data: sorted.map(d => d[1]), 
                backgroundColor: ["#2563eb","#16a34a","#f59e0b","#dc2626","#7c3aed","#0ea5e9","#14b8a6","#e11d48"] 
            }] 
        }
    });
}

function updateGlobalStats() {
    const trendMap = {};
    const countryStats = {};
    const data = groupByTrend(filterByDateTime([...allData]));

    data.forEach(d => {
        if (!trendMap[d.trend]) trendMap[d.trend] = {};
        trendMap[d.trend][d.country] = d.tweet_count;

        if (!countryStats[d.country]) countryStats[d.country] = { sum:0, count:0 };
        countryStats[d.country].sum += d.tweet_count;
        countryStats[d.country].count++;
    });

    const topTrends = Object.entries(trendMap)
        .map(([trend,countries])=>({trend,count:Object.keys(countries).length,countries}))
        .sort((a,b)=>b.count-a.count)
        .slice(0,5);

    document.getElementById("globalTrend").innerHTML = topTrends.map((t,i)=>`
        <p class="trend-item" onclick='openTrendModal(${JSON.stringify(t.countries)},"${t.trend}")'>
            ${i+1}. <strong>${t.trend}</strong> <span>(${t.count} países)</span>
        </p>
    `).join("");

    const topCountries = Object.entries(countryStats)
        .map(([c,v])=>({country:c,avg:v.sum/v.count}))
        .sort((a,b)=>b.avg-a.avg)
        .slice(0,5);

    document.getElementById("topCountry").innerHTML = `
        <ol style="margin: 0 auto; width: fit-content; text-align: left;">
            ${topCountries.map(c=>`<li>${translateCountry(c.country)} — ${formatNumber(Math.round(c.avg))} tweets</li>`).join("")}
        </ol>
    `;
}

// =======================================
// COMPARADOR
// =======================================
function compareCountries() {
    const c1 = document.getElementById("country1").value;
    const c2 = document.getElementById("country2").value;
    if(!c1||!c2) return;

    const buildStats = country => {
        const data = groupByTrend(filterByDateTime(allData)).filter(d=>d.country===country);
        if(data.length===0) return {trends:0,tweets:0,top:"Sin datos"};
        return {
            trends: data.length,
            tweets: data.reduce((s,d)=>s+d.tweet_count,0),
            top: [...data].sort((a,b)=>b.tweet_count-a.tweet_count)[0].trend
        };
    };

    const s1 = buildStats(c1);
    const s2 = buildStats(c2);

    document.getElementById("c1Title").textContent = translateCountry(c1);
    document.getElementById("c2Title").textContent = translateCountry(c2);

    document.getElementById("c1Trends").textContent = s1.trends;
    document.getElementById("c2Trends").textContent = s2.trends;

    document.getElementById("c1Tweets").textContent = formatNumber(s1.tweets);
    document.getElementById("c2Tweets").textContent = formatNumber(s2.tweets);

    document.getElementById("c1Top").textContent = s1.top;
    document.getElementById("c2Top").textContent = s2.top;
}

// =======================================
// TABS
// =======================================
function setupTabs() {
    document.querySelectorAll(".tab-btn").forEach(btn=>{
        btn.addEventListener("click",()=>{
            document.querySelectorAll(".tab-btn").forEach(b=>b.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c=>c.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById(btn.dataset.tab).classList.add("active");
            if(btn.dataset.tab==="tab-charts") updateDashboard();
        });
    });
}

// =======================================
// MODAL
// =======================================
function openTrendModal(countries,trend){
    const modal=document.getElementById("trendModal");
    const title=document.getElementById("modalTitle");
    const list=document.getElementById("modalList");

    title.textContent=`🌍 ${trend}`;
    list.innerHTML=Object.entries(countries)
        .sort((a,b)=>b[1]-a[1])
        .map(([c,v])=>`<li>${translateCountry(c)}: ${formatNumber(v)} tweets</li>`).join("");

    modal.classList.remove("hidden");
}

document.getElementById("closeModal").onclick=()=>document.getElementById("trendModal").classList.add("hidden");
window.onclick=e=>{if(e.target===document.getElementById("trendModal"))document.getElementById("trendModal").classList.add("hidden");};

// =======================================
// TOAST
// =======================================
function showToast(message) {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
    }, 2500);
}

function validateDateTimeFilters(startDate, startTime, endDate, endTime) {
    const sDateTime = new Date(startDate + "T" + (startTime || "00:00"));
    const eDateTime = new Date(endDate + "T" + (endTime || "23:59"));

    if (sDateTime > eDateTime) {
        showToast("⚠️ La fecha y hora de inicio no puede ser posterior a la de fin");
        return false;
    }
    return true;
}

function getFilteredDataForAI() {
    return filterByDateTime([...allData]);
}

