/* Daily Briefing Dashboard
   Reads docs/data.json (90-day rolling history)
   Rendered by GitHub Pages — no build step */

/* ── PIN Guard ── */
(function () {
  const H = "e401f2bd399f3456e5348217a7908ca545ea6d179f60f297a1b0133e87d2ff85";
  async function hash(s) {
    const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
    return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
  }
  if (sessionStorage.getItem("db_auth") === "1") {
    document.getElementById("pin-screen").style.display = "none";
    document.getElementById("dashboard").style.display = "";
    return;
  }
  let input = "";
  const dots = document.querySelectorAll(".dot");
  const err  = document.getElementById("pin-error");

  function updateDots() {
    dots.forEach((d, i) => d.classList.toggle("filled", i < input.length));
  }

  async function submit() {
    if ((await hash(input)) === H) {
      sessionStorage.setItem("db_auth", "1");
      document.getElementById("pin-screen").style.display = "none";
      document.getElementById("dashboard").style.display = "";
      main().catch(console.error); // PIN 인증 후 대시보드 표시된 상태에서 실행
    } else {
      err.textContent = "PIN이 틀렸어요";
      input = "";
      updateDots();
      setTimeout(() => { err.textContent = ""; }, 1500);
    }
  }

  document.getElementById("pin-keypad").addEventListener("click", async (e) => {
    const key = e.target.closest(".key");
    if (!key) return;
    if (key.id === "key-del") {
      input = input.slice(0, -1);
      updateDots();
      return;
    }
    const n = key.dataset.n;
    if (n === undefined) return;
    if (input.length >= 4) return;
    input += n;
    updateDots();
    if (input.length === 4) await submit();
  });

  document.addEventListener("keydown", async (e) => {
    if (document.getElementById("pin-screen").style.display === "none") return;
    if (e.key >= "0" && e.key <= "9") {
      if (input.length >= 4) return;
      input += e.key;
      updateDots();
      if (input.length === 4) await submit();
    } else if (e.key === "Backspace") {
      input = input.slice(0, -1);
      updateDots();
    }
  });
})();

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

/* ── 섹터 방향 ── */
function renderSectors(latest) {
  const container = document.getElementById("sector-bars");
  if (!container) return;
  const sectors = latest.sectors;
  if (!sectors || !sectors.length) {
    container.innerHTML = `<p class="num-sm" style="color:var(--muted)">데이터 없음</p>`;
    return;
  }
  const maxAbs = Math.max(...sectors.map(s => Math.abs(s.pct)), 0.01);
  container.innerHTML = "";
  sectors.forEach(s => {
    const isUp = s.pct >= 0;
    const barW = (Math.abs(s.pct) / maxAbs * 50).toFixed(1);
    const el = document.createElement("div");
    el.className = "sector-row";
    el.innerHTML = `
      <span class="sector-name">${s.name}</span>
      <div class="sector-bar-track">
        <div class="sector-bar-fill ${isUp ? "up" : "down"}" style="width:${barW}%"></div>
      </div>
      <span class="sector-pct ${isUp ? "up" : "down"}">${s.pct > 0 ? "+" : ""}${s.pct.toFixed(2)}%</span>`;
    container.appendChild(el);
  });
}

/* ── 신호 시스템 ── */
function renderSignal(latest) {
  const el = document.getElementById("signal-content");
  if (!el) return;
  const sig = latest.signal;
  if (!sig || !sig.signal) {
    el.innerHTML = `<p class="num-sm" style="color:var(--muted)">데이터 없음</p>`;
    return;
  }
  const cls = sig.signal === "BUY" ? "signal-buy" : sig.signal === "SELL" ? "signal-sell" : "signal-hold";
  const gaugeColor = sig.signal === "BUY" ? "var(--up)" : sig.signal === "SELL" ? "var(--down)" : "var(--gold)";
  el.innerHTML = `
    <div class="signal-badge-row">
      <span class="signal-badge ${cls}">${sig.signal}</span>
      <span class="signal-score">${sig.score}<span style="font-size:.72em;opacity:.55">/100</span></span>
    </div>
    <div class="signal-gauge-wrap">
      <div class="signal-gauge-bar" style="width:${sig.score}%;background:${gaugeColor}"></div>
    </div>
    ${sig.reason ? `<p class="signal-reason">${sig.reason}</p>` : ""}
    ${sig.top_risk ? `<p class="signal-risk">⚠️ ${sig.top_risk}</p>` : ""}`;
}

/* ── AI 검증 (분석가 → 비평가) ── */
function renderAiVerification(latest) {
  const el = document.getElementById("ai-verification-content");
  if (!el) return;
  const sig = latest.signal;
  if (!sig || !sig.analyst_signal) {
    el.innerHTML = `<p class="num-sm" style="color:var(--muted)">데이터 없음</p>`;
    return;
  }
  const aCls = sig.analyst_signal === "BUY" ? "signal-buy" : sig.analyst_signal === "SELL" ? "signal-sell" : "signal-hold";
  const fCls = sig.signal === "BUY" ? "signal-buy" : sig.signal === "SELL" ? "signal-sell" : "signal-hold";
  el.innerHTML = `
    <div class="verif-stage">
      <span class="verif-label">분석가</span>
      <span class="signal-badge ${aCls} signal-badge-sm">${sig.analyst_signal}</span>
      <span class="verif-score">${sig.analyst_score}/100</span>
    </div>
    ${sig.critique ? `<p class="verif-critique">${sig.critique}</p>` : ""}
    <div class="verif-stage" style="margin-top:.75rem">
      <span class="verif-label">비평가 → 최종</span>
      <span class="signal-badge ${fCls} signal-badge-sm">${sig.signal}</span>
      <span class="verif-score">${sig.score}/100</span>
    </div>
    ${latest.ai_analysis ? `
    <details class="ai-analysis-details">
      <summary>AI 심층 분석 보기</summary>
      <pre class="ai-analysis-text">${latest.ai_analysis}</pre>
    </details>` : ""}`;
}

/* ── 추천 이력 + 트리플 배리어 ── */
function renderRecommendations(recos) {
  const summary = document.getElementById("reco-summary");
  const tbody   = document.getElementById("reco-tbody");
  if (!tbody) return;

  if (!recos || !recos.length) {
    if (summary) summary.innerHTML = `<p class="num-sm" style="color:var(--muted);margin-bottom:.75rem">아직 추천 이력이 없습니다</p>`;
    return;
  }

  const closed   = recos.filter(r => r.outcome);
  const wins     = closed.filter(r => r.outcome === "WIN").length;
  const losses   = closed.filter(r => r.outcome === "LOSS").length;
  const neutrals = closed.filter(r => r.outcome === "NEUTRAL").length;
  const winRate  = closed.length ? (wins / closed.length * 100).toFixed(0) : "—";
  const avgRet   = closed.length
    ? (closed.reduce((s, r) => s + (r.outcome_return ?? 0), 0) / closed.length).toFixed(2)
    : null;

  if (summary) {
    summary.innerHTML = `
      <div class="reco-stats">
        <div class="reco-stat"><span class="reco-stat-label">승률</span><span class="reco-stat-val">${winRate}%</span></div>
        <div class="reco-stat"><span class="reco-stat-label">WIN</span><span class="reco-stat-val up">${wins}</span></div>
        <div class="reco-stat"><span class="reco-stat-label">LOSS</span><span class="reco-stat-val down">${losses}</span></div>
        <div class="reco-stat"><span class="reco-stat-label">중립</span><span class="reco-stat-val" style="color:var(--gold)">${neutrals}</span></div>
        ${avgRet !== null ? `<div class="reco-stat"><span class="reco-stat-label">평균 수익률</span><span class="reco-stat-val ${Number(avgRet) >= 0 ? "up" : "down"}">${Number(avgRet) > 0 ? "+" : ""}${avgRet}%</span></div>` : ""}
      </div>`;
  }

  tbody.innerHTML = "";
  recos.slice().reverse().slice(0, 30).forEach(r => {
    const outCls = r.outcome === "WIN" ? "up" : r.outcome === "LOSS" ? "down" : "";
    const sigCls = r.signal === "BUY" ? "signal-buy" : r.signal === "SELL" ? "signal-sell" : "signal-hold";
    const fmtN   = (v) => v != null ? Number(v).toLocaleString("ko-KR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "—";
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.date}</td>
      <td><span class="signal-badge ${sigCls} signal-badge-sm">${r.signal}</span></td>
      <td>${r.score}</td>
      <td>${fmtN(r.sp500_entry)}</td>
      <td class="up">${fmtN(r.sp500_tp)}</td>
      <td class="down">${fmtN(r.sp500_sl)}</td>
      <td class="${outCls}">${r.outcome || "—"}</td>
      <td class="${outCls}">${r.outcome_return != null ? (r.outcome_return > 0 ? "+" : "") + r.outcome_return + "%" : "—"}</td>`;
    tbody.appendChild(tr);
  });
}

/* ── Chart.js 공통 옵션 ── */
const TOOLTIP = {
  backgroundColor: "#1e293b",
  titleColor: "#94a3b8",
  bodyColor: "#e2e8f0",
  borderColor: "rgba(255,255,255,0.18)",
  borderWidth: 1,
  padding: 10,
  caretSize: 5,
};

const INTERACTION = {
  mode: "index",
  intersect: false,
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

function makeLineChart(id, labels, values, color, fmtVal) {
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
      interaction: INTERACTION,
      plugins: {
        legend: { display: false },
        tooltip: {
          ...TOOLTIP,
          callbacks: {
            label: (item) => fmtVal ? fmtVal(item.raw) : ` ${Number(item.raw).toLocaleString("ko-KR")}`,
          },
        },
      },
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
      interaction: INTERACTION,
      plugins: {
        legend: { display: false },
        tooltip: {
          ...TOOLTIP,
          callbacks: {
            label: (item) => item.raw !== null ? ` ${item.raw > 0 ? "+" : ""}${Number(item.raw).toFixed(2)}%` : "",
          },
        },
      },
      scales: SCALE_OPTS(v => v.toFixed(1) + "%"),
    },
  });
}

/* ── 지수 추세 차트 4개 ── */
function renderIndexCharts(data) {
  const labels = data.map(d => d.date.slice(5));
  makeLineChart("chart-KOSPI",  labels, data.map(d => d.stocks.KOSPI?.close  ?? null), "#818cf8", v => ` ${Number(v).toLocaleString("ko-KR")}`);
  makeLineChart("chart-SP500",  labels, data.map(d => d.stocks.SP500?.close  ?? null), "#34d399", v => ` ${Number(v).toLocaleString("ko-KR")}`);
  makeLineChart("chart-NASDAQ", labels, data.map(d => d.stocks.NASDAQ?.close ?? null), "#60a5fa", v => ` ${Number(v).toLocaleString("ko-KR")}`);
  makeLineChart("chart-USD",    labels, data.map(d => d.fx?.USD_KRW           ?? null), "#f59e0b", v => ` ${Number(v).toFixed(2)} 원`);
}

/* ── 탭 전환 ── */
function initTabs(data) {
  const btns   = document.querySelectorAll(".tab-btn");
  const panels = document.querySelectorAll(".tab-panel");

  btns.forEach(btn => {
    btn.addEventListener("click", () => {
      btns.forEach(b => b.classList.remove("active"));
      panels.forEach(p => p.classList.remove("active"));
      btn.classList.add("active");

      const panel = document.querySelector(`.tab-panel[data-tab="${btn.dataset.tab}"]`);
      if (panel) {
        panel.classList.add("active");
        if (btn.dataset.tab === "portfolio" && !panel.dataset.rendered) {
          panel.dataset.rendered = "1";
          renderPortfolioChart(data);
        }
      }
    });
  });
}

/* ── 메인 ── */
async function main() {
  const [data, recos] = await Promise.all([
    fetch("data.json").then(r => r.json()),
    fetch("recommendations.json").then(r => r.json()).catch(() => []),
  ]);
  if (!data.length) return;

  const latest = data[data.length - 1];
  document.getElementById("date-label").textContent = latest.date + " 기준";

  renderStocks(latest);
  renderFx(latest);
  renderPortfolioSummary(latest);
  renderHoldings(latest);
  renderIndexCharts(data);
  renderNews(latest);
  renderPortfolioNews(latest);
  renderSectors(latest);
  renderSignal(latest);
  renderAiVerification(latest);
  renderRecommendations(recos);
  initTabs(data);
}

if (sessionStorage.getItem("db_auth") === "1") {
  main().catch(console.error);
}
