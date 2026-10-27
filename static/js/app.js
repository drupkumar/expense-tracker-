const mint = "#3ee0b0";
const rose = "#ff8b7a";
const gold = "#e8c07a";

function lineChart(id, labels, a, b) {
  const el = document.getElementById(id);
  if (!el || typeof Chart === "undefined") return;
  new Chart(el, {
    type: "line",
    data: {
      labels,
      datasets: [
        { label: "Income", data: a, borderColor: mint, backgroundColor: "rgba(62,224,176,0.12)", fill: true, tension: 0.4 },
        { label: "Expense", data: b, borderColor: rose, backgroundColor: "rgba(255,139,122,0.1)", fill: true, tension: 0.4 },
      ],
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

document.addEventListener("DOMContentLoaded", () => {
  const dash = window.AUREUM_CHARTS;
  if (dash) {
    lineChart("trendChart", dash.trendLabels, dash.trendIncome, dash.trendExpense);
    doughnut("catChart", dash.catLabels, dash.catValues, dash.catColors);
  }
  const reports = window.AUREUM_REPORTS;
  if (reports) {
    lineChart("yearChart", reports.months, reports.income, reports.expense);
    doughnut("mixChart", reports.cats, reports.catVals, [mint, gold, rose, "#64b5f6", "#ce93d8", "#ffd54f", "#80cbc4", "#ef9a9a"]);
  }
  setTimeout(() => {
    document.querySelectorAll(".flash").forEach((n) => {
      n.style.opacity = "0";
      n.style.transition = "opacity .4s";
    });
  }, 4200);
});
