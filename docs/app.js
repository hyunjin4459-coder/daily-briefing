/* Daily Briefing Dashboard
   Reads docs/data.json (90-day rolling history)
   Rendered by GitHub Pages — no build step */

const STOCK_LABELS = {
  KOSPI:  "KOSPI",
  KOSDAQ: "KOSDAQ",
  SP500:  "S&P 500",
  NASDAQ: "NASDAQ",
  DOW:    "다우",
};

const fmt    = (n, d = 2) => n.toLocaleString("ko-KR", { minimumFractionDigits: d, maximumFractionDigits: d });
const arrow  = (v) => (v >= 0 ? "▲" : "▼");
const updown = (v) => (v >= 0 ? "up" : "down");

/* ── 지수 카드 ── */
function renderStocks(latest) {
  const grid = document.getElementById("stock-cards");
  grid.innerHTML = "";
  for (const [key, label] of Object.entries(STOCK_LABELS)) {
    const s = latest.stocks[key];
    if (!s) continue;
    const el = document.createElement("div");
    el.className = "card";
    el.innerHTML = `
      <p class="index-name">${label}</p>
      <p class="num-lg">${fmt(s.close)}</p>
      <p class="num-sm ${updown(s.pct)}" style="margin-top:.3rem">
        ${arrow(s.pct)} ${Math.abs(s.change).toFixed(2)}
        <span style="opacity:.65">&thinsp;(${s.pct > 0 ? "+" : ""}${s.pct.toFixed(2)}%)</span>
      </p>`;
    grid.appendChild(el);
  }
}

/* ── 환율 카드 ── */
function renderFx(latest) {
  document.getElementById("fx-usd").innerHTML = `
    <p class="card-label">USD / KRW</p>
    <p class="num-xl">${fmt(latest.fx.USD_KRW)}</p>`;
  document.getElementById("fx-jpy").innerHTML = `
    <p class="card-label">JPY / KRW</p>
    <p class="num-xl">${latest.fx.JPY_KRW.toFixed(2)}</p>`;
}

/* ── 포트폴리오 요약 ── */
function renderPortfolioSummary(latest) {
  const el = document.getElementById("portfolio-total");
  const pf = latest.portfolio;
  if (!pf) {
    el.innerHTML = `<p class="card-label">💼 포트폴리오</p>
      <p class="num-sm" style="color:var(--muted)">데이터 없음</p>`;
    return;
  }
  const pos = pf.total_pnl >= 0;
  el.innerHTML = `
    <p class="card-label">💼 포트폴리오 (토스증권)</p>
    <div class="pf-total-row">
      <span class="num-xl">$${fmt(pf.total_value)}</span>
      <span class="pf-badge ${pos ? "up" : "down"}">
        ${arrow(pf.total_pnl)}&thinsp;$${fmt(Math.abs(pf.total_pnl))}
        &ensp;${pf.total_pnl_pct > 0 ? "+" : ""}${pf.total_pnl_pct.toFixed(2)}%
      </span>
    </div>`;
}

/* ── 종목별 카드 ── */
function renderHoldings(latest) {
  const grid = document.getElementById("holdings-cards");
  grid.innerHTML = "";
  const holdings = latest.portfolio?.holdings ?? [];
  holdings
    .slice()
    .sort((a, b) => b.value - a.value)
    .forEach(h => {
      const el = document.createElement("div");
      el.className = "card";
      el.innerHTML = `
        <p class="holding-ticker">${h.ticker}</p>
        <p class="holding-name">${h.name}</p>
        <p class="num-lg" style="margin-top:.5rem">$${h.current_price.toFixed(2)}</p>
        <p class="num-sm ${updown(h.pnl_pct)}" style="margin-top:.25rem">
          ${arrow(h.pnl_pct)} ${Math.abs(h.pnl_pct).toFixed(1)}%
          <span style="opacity:.65">&thinsp;($${fmt(h.value, 0)})</span>
        </p>
        <p class="holding-entry">진입 $${h.avg_price.toFixed(2)}</p>`;
      grid.appendChild(el);
    });
}

/* ── 뉴스 섹션 ── */
function renderNewsSection(id, items) {
  const ul = document.getElementById(id);
  if (!ul) return;
  ul.innerHTML = "";
  (items || []).forEach((item, i) => {
    const title = typeof item === "string" ? item : item.title;
    const li = document.createElement("li");
    li.className = "news-item";
    li.innerHTML = `<span class="news-num">${i + 1}.</span><span>${title}</span>`;
    ul.appendChild(li);
  });
}

function renderNews(latest) {
  renderNewsSection("news-economy",    latest.news?.economy);
  renderNewsSection("news-realestate", latest.news?.realestate);
  renderNewsSection("news-global",     latest.news?.global);
  renderNewsSection("news-usnews",     latest.news?.usnews);
}

/* ── 종목별 뉴스 ── */
function renderPortfolioNews(latest) {
  const grid = document.getElementById("portfolio-news-grid");
  if (!grid) return;
  const pfNews = latest.portfolio_news;
  if (!pfNews || !Object.keys(pfNews).length) {
    grid.innerHTML = `<p class="num-sm" style="color:var(--muted)">데이터 없음 — 내일 10시 이후 갱신</p>`;
    return;
  }
  grid.innerHTML = "";
  for (const [ticker, info] of Object.entries(pfNews)) {
    const col = document.createElement("div");
    col.className = "card";
    const newsHtml = (info.items || [])
      .map(it => `<p class="pf-news-item">${it.title}</p>`)
      .join("");
    col.innerHTML = `<p class="pf-news-ticker">[${ticker}] ${info.name}</p>${newsHtml}`;
    grid.appendChild(col);
  }
}

/* ── Chart.js 공통 옵션 ── */
const TOOLTIP = {
  backgroundColor: "#1e293b",
  titleColor: "#94a3b8",
  bodyColor: "#e2e8f0",
  borderColor: "rgba(255,255,255,0.08)",
  borderWidth: 1,
};

const SCALE_OPTS = (cbY) => ({
  x: {
    ticks: { color: "#475569", font: { size: 9 }, maxTicksLimit: 7 },
    grid:  { color: "rgba(255,255,255,0.04)" },
  },
  y: {
    ticks: {
      color: "#475569",
      font: { size: 9 },
      ...(cbY ? { callback: cbY } : {}),
    },
    grid: { color: "rgba(255,255,255,0.04)" },
  },
});

function makeLineChart(id, labels, values, color) {
  const ctx = document.getElementById(id);
  if (!ctx) return;
  new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        data: values,
        borderColor: color,
        backgroundColor: color + "18",
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        fill: true,
        tension: 0.35,
        spanGaps: true,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 500 },
      plugins: { legend: { display: false }, tooltip: { ...TOOLTIP } },
      scales: SCALE_OPTS(),
    },
  });
}

/* ── 포트폴리오 90일 수익률 차트 ── */
function renderPortfolioChart(data) {
  const ctx = document.getElementById("chart-portfolio");
  if (!ctx) return;
  const labels = data.map(d => d.date.slice(5));
  const values = data.map(d => d.portfolio?.total_pnl_pct ?? null);
  const last   = values.findLast(v => v !== null) ?? 0;
  const color  = last >= 0 ? "#10b981" : "#f43f5e";
  const fill   = last >= 0 ? "rgba(16,185,129,0.08)" : "rgba(244,63,94,0.08)";
  new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "수익률 (%)",
        data: values,
        borderColor: color,
        backgroundColor: fill,
        borderWidth: 2.5,
        pointRadius: 0,
        pointHoverRadius: 5,
        fill: true,
        tension: 0.35,
        spanGaps: true,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 500 },
      plugins: { legend: { display: false }, tooltip: { ...TOOLTIP } },
      scales: SCALE_OPTS(v => v.toFixed(1) + "%"),
    },
  });
}

/* ── 지수 추세 차트 4개 ── */
function renderIndexCharts(data) {
  const labels = data.map(d => d.date.slice(5));
  makeLineChart("chart-KOSPI",  labels, data.map(d => d.stocks.KOSPI?.close  ?? null), "#818cf8");
  makeLineChart("chart-SP500",  labels, data.map(d => d.stocks.SP500?.close  ?? null), "#34d399");
  makeLineChart("chart-NASDAQ", labels, data.map(d => d.stocks.NASDAQ?.close ?? null), "#60a5fa");
  makeLineChart("chart-USD",    labels, data.map(d => d.fx?.USD_KRW           ?? null), "#f59e0b");
}

/* ── 메인 ── */
async function main() {
  const data = await fetch("data.json").then(r => r.json());
  if (!data.length) return;

  const latest = data[data.length - 1];
  document.getElementById("date-label").textContent = latest.date + " 기준";

  renderStocks(latest);
  renderFx(latest);
  renderPortfolioSummary(latest);
  renderHoldings(latest);
  renderPortfolioChart(data);
  renderIndexCharts(data);
  renderNews(latest);
  renderPortfolioNews(latest);
}

main().catch(console.error);
