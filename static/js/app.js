const mint = "#3ee0b0";
const rose = "#ff8b7a";
const gold = "#e8c07a";

function lineChart(id, labels, a, b, forecast = null) {
  const el = document.getElementById(id);
  if (!el || typeof Chart === "undefined") return;
  const datasets = [
    { label: "Income", data: a, borderColor: mint, backgroundColor: "rgba(62,224,176,0.12)", fill: true, tension: 0.4 },
    { label: "Expense", data: b, borderColor: rose, backgroundColor: "rgba(255,139,122,0.1)", fill: true, tension: 0.4 },
  ];
  if (forecast !== null && forecast > 0) {
    const forecastData = new Array(labels.length).fill(null);
    forecastData[labels.length - 1] = b[b.length - 1] || 0;
    forecastData.push(forecast);
    datasets.push({
      label: "Forecast",
      data: forecastData,
      borderColor: gold,
      borderDash: [5, 5],
      borderDashOffset: 0,
      borderWidth: 2,
      pointRadius: 0,
      fill: false,
    });
  }
  new Chart(el, {
    type: "line",
    data: {
      labels: forecast !== null ? [...labels, "Forecast"] : labels,
      datasets,
    },
    options: {
      plugins: { legend: { labels: { color: "#cfe7de" } } },
      scales: {
        x: { ticks: { color: "#93b0a6" }, grid: { color: "rgba(255,255,255,0.04)" } },
        y: { ticks: { color: "#93b0a6" }, grid: { color: "rgba(255,255,255,0.04)" } },
      },
    },
  });
}

function doughnut(id, labels, values, colors) {
  const el = document.getElementById(id);
  if (!el || typeof Chart === "undefined") return;
  new Chart(el, {
    type: "doughnut",
    data: {
      labels: labels.length ? labels : ["No data"],
      datasets: [{ data: values.length ? values : [1], backgroundColor: colors.length ? colors : ["#16352c"], borderWidth: 0 }],
    },
    options: {
      cutout: "64%",
      plugins: { legend: { position: "bottom", labels: { color: "#cfe7de", boxWidth: 12 } } },
    },
  });
}

function merchantBars(labels, values) {
  const el = document.getElementById("merchantChart");
  if (!el || typeof Chart === "undefined") return;
  new Chart(el, { type: "bar", data: { labels, datasets: [{ label: "Expenses", data: values, backgroundColor: mint, borderRadius: 8 }] },
    options: { indexAxis: "y", plugins: { legend: { display: false } }, scales: {
      x: { ticks: { color: "#93b0a6" }, grid: { color: "rgba(255,255,255,0.04)" } },
      y: { ticks: { color: "#cfe7de" }, grid: { display: false } },
    } } });
}

document.addEventListener("DOMContentLoaded", () => {
  const showLoading = () => document.body.classList.add("page-loading");
  document.addEventListener("click", (event) => {
    const link = event.target.closest("a[href]");
    if (!link || link.target === "_blank" || link.hasAttribute("download") || link.dataset.bsToggle || link.getAttribute("href").startsWith("#")) return;
    const destination = new URL(link.href, window.location.href);
    if (destination.origin === window.location.origin && destination.href !== window.location.href) showLoading();
  });
  document.addEventListener("submit", (event) => {
    if (event.target.method.toLowerCase() !== "dialog") showLoading();
  });
  if (window.location.hash === "#addModal") {
    const modal = document.getElementById("addModal");
    if (modal && window.bootstrap) new bootstrap.Modal(modal).show();
  }
  const dash = window.AUREUM_CHARTS;
  if (dash) {
    lineChart("trendChart", dash.trendLabels, dash.trendIncome, dash.trendExpense, dash.forecast);
    doughnut("catChart", dash.catLabels, dash.catValues, dash.catColors);
  }
  const reports = window.AUREUM_REPORTS;
  if (reports) {
    lineChart("yearChart", reports.months, reports.income, reports.expense, reports.forecast);
    doughnut("mixChart", reports.cats, reports.catVals, [mint, gold, rose, "#64b5f6", "#ce93d8", "#ffd54f", "#80cbc4", "#ef9a9a"]);
    merchantBars(reports.merchantLabels, reports.merchantValues);
  }
  setTimeout(() => {
    document.querySelectorAll(".flash").forEach((n) => {
      n.style.opacity = "0";
      n.style.transition = "opacity .4s";
    });
  }, 4200);
});
