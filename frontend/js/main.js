let allData = [];
let trendsChart = null;
let countryChart = null;

let startDate = null;
let endDate = null;
let startTime = null;
let endTime = null;

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
    spain: "España"
};

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
        startDate = document.getElementById("startDate").value || defaultStartDate;
        endDate = document.getElementById("endDate").value || defaultEndDate;
        startTime = document.getElementById("startTime").value || defaultStartTime;
        endTime = document.getElementById("endTime").value || defaultEndTime;

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

    setupTabs();
});

/* =======================
   CARGA Y PARSEO
======================= */
async function loadData() {
    const response = await fetch("../tendencias.csv");
    const text = await response.text();
    allData = parseCSV(text);
    populateCountrySelector();
    updateDashboard();
    showLastUpdate();
}

function parseCSV(data) {
    const lines = data.trim().split("\n");
    lines.shift();
    return lines.map(line => {
        const parts = line.split(",");
        return {
            fecha: parts[0].trim(),
            hora: parts[1].trim(),
            trend: parts[2].trim(),
            tweet_count: parseInt(parts[3]) || 0,
            country: parts[4].trim().toLowerCase()
        };
    });
}

/* =======================
   UTILIDAD: AGRUPAR TENDENCIAS
======================= */
function groupByTrend(data) {
    const grouped = {};
    data.forEach(d => {
        const key = d.trend + '||' + d.country;
        if (!grouped[key]) grouped[key] = { ...d };
        else grouped[key].tweet_count += d.tweet_count;
    });
    return Object.values(grouped);
}

/* =======================
   SELECTORES
======================= */
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

/* =======================
   FILTRO FECHA + HORA
======================= */
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

/* =======================
   DASHBOARD Y GRÁFICOS
======================= */
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
    compareCountries(); // refresca comparador automáticamente
}

/* =======================
   GRÁFICOS
======================= */
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
            scales: { y: { ticks: { callback: value => formatNumber(value) } } }
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
        data: { labels: sorted.map(d => translateCountry(d[0])), datasets: [{ data: sorted.map(d => d[1]), backgroundColor: ["#2563eb","#16a34a","#f59e0b","#dc2626","#7c3aed","#0ea5e9","#14b8a6","#e11d48"] }] }
    });
}

/* =======================
   DASHBOARD GLOBAL
======================= */
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

/* =======================
   COMPARADOR
======================= */
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

/* =======================
   TABS
======================= */
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

/* =======================
   UTILIDADES
======================= */
function translateCountry(code){return countryMap[code]||code;}
function formatNumber(num){return num.toLocaleString("es-ES");}

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

/* =======================
   TOAST
======================= */
function showToast(message) {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
    }, 2500);
}
