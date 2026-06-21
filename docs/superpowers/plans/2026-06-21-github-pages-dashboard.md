# GitHub Pages 마켓 브리핑 대시보드 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `docs/data.json`의 90일 누적 시장 데이터를 읽어 GitHub Pages에서 다크 벤토 대시보드로 표시한다.

**Architecture:** 완전 정적 사이트. `docs/` 아래 `index.html`, `style.css`, `app.js` 세 파일. `app.js`가 `data.json`을 fetch해 DOM을 그린다. Python 측은 `portfolio_news`를 `data.json`에 함께 저장하도록 `save_data()` 를 수정한다.

**Tech Stack:** HTML5, CSS Custom Properties, Vanilla JS (ES2022), Chart.js 4.4 (CDN)

## Global Constraints

- 빌드 도구 없음 — `<script src="app.js">` + `<link href="style.css">` 직접 참조
- CDN Chart.js: `https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js`
- TailwindCSS CDN 사용하지 않음 — 모든 스타일은 `style.css` CSS Custom Properties
- 브라우저 테스트 서버: `python -m http.server 8080` (docs/ 폴더에서 실행)
- 프로젝트 경로: `C:\Users\지니\OneDrive\Desktop\code\2026_0620_kakao-briefing\`
- `data.json` 경로: `docs/data.json` — GitHub Actions가 매일 덮어씀 (건드리지 말 것)

---

### Task 1: Python — portfolio_news를 data.json에 저장

**Files:**
- Modify: `src/main.py`

**Interfaces:**
- Consumes: `portfolio_news: dict` — `{"JOBY": {"name": "조비 에비에이션", "items": [{"title":"…","desc":"…"}]}, …}`
- Produces: `data.json` 각 엔트리에 `"portfolio_news"` 키 포함

- [ ] **Step 1: `save_data()` 시그니처 + 엔트리 구조 수정**

`src/main.py`의 `save_data` 함수 전체를 교체:

```python
def save_data(stocks: dict, fx: dict, news: dict, portfolio: dict | None = None, portfolio_news: dict | None = None) -> None:
    today = datetime.date.today().isoformat()
    entry = {
        "date": today,
        "stocks": stocks,
        "fx": fx,
        "news": news,
        "portfolio": portfolio,
        "portfolio_news": portfolio_news or {},
    }
    existing = json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else []
    existing = [e for e in existing if e["date"] != today]
    existing.append(entry)
    existing = existing[-90:]
    DATA_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[main] 데이터 저장 완료 ({len(existing)}일치)")
```

- [ ] **Step 2: `run()`에서 `portfolio_news`를 `save_data`에 전달**

`run()` 내부의 save_data 호출 줄을 교체:

```python
    print("[main] 대시보드 데이터 저장 중...")
    save_data(stocks, fx, news, portfolio, portfolio_news)
```

- [ ] **Step 3: 로컬 실행으로 검증**

```bash
cd C:\Users\지니\OneDrive\Desktop\code\2026_0620_kakao-briefing
python -m src.main
```

`docs/data.json` 열어서 최신 엔트리에 아래 구조 확인:

```json
{
  "date": "2026-06-21",
  "portfolio_news": {
    "JOBY": {"name": "조비 에비에이션", "items": [{"title": "…", "desc": "…"}]},
    "QQQ":  {"name": "QQQ",            "items": [{"title": "…", "desc": "…"}]}
  }
}
```

- [ ] **Step 4: 커밋**

```bash
git add src/main.py docs/data.json
git commit -m "feat: portfolio_news를 data.json에 저장"
git push
```

---

### Task 2: HTML + CSS 디자인 셸

**Files:**
- Modify: `docs/index.html` (전체 교체)
- Create: `docs/style.css`

**DOM id 계약** — Task 3-5의 `app.js`가 아래 id에 의존:

| id | 역할 |
|----|------|
| `date-label` | 날짜 텍스트 |
| `stock-cards` | 지수 카드 5개 컨테이너 |
| `fx-usd`, `fx-jpy` | 환율 카드 |
| `portfolio-total` | 포트폴리오 요약 |
| `holdings-cards` | 종목별 카드 컨테이너 |
| `chart-portfolio` | 90일 수익률 canvas |
| `chart-KOSPI`, `chart-SP500`, `chart-NASDAQ`, `chart-USD` | 지수 추세 canvas |
| `news-economy`, `news-realestate`, `news-global`, `news-usnews` | 뉴스 ul |
| `portfolio-news-grid` | 종목별 뉴스 컨테이너 |

- [ ] **Step 1: `docs/style.css` 생성**

```css
/* ── Design Tokens ── */
:root {
  --bg:         #070d1a;
  --bg-card:    rgba(255, 255, 255, 0.04);
  --border:     rgba(255, 255, 255, 0.07);
  --text:       #e2e8f0;
  --muted:      #475569;
  --up:         #10b981;
  --down:       #f43f5e;
  --accent:     #818cf8;
  --gold:       #f59e0b;
  --r-lg:       1.25rem;
  --r-md:       0.875rem;
  --dur:        180ms;
  --ease:       cubic-bezier(0.16, 1, 0.3, 1);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans KR", sans-serif;
  min-height: 100vh;
  line-height: 1.5;
}

/* ── Wrapper ── */
.wrapper {
  max-width: 1120px;
  margin: 0 auto;
  padding: 2rem 1.25rem 5rem;
}

/* ── Header ── */
.header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 2.5rem;
}

.title {
  font-size: clamp(1.6rem, 3vw, 2.4rem);
  font-weight: 800;
  letter-spacing: -0.04em;
  background: linear-gradient(135deg, #818cf8 0%, #a78bfa 55%, #c084fc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  font-size: 0.78rem;
  color: var(--muted);
  margin-top: 0.3rem;
}

.badge {
  font-size: 0.7rem;
  color: var(--muted);
  border: 1px solid var(--border);
  border-radius: 2rem;
  padding: 0.3rem 0.8rem;
  white-space: nowrap;
}

/* ── Card ── */
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 1.2rem;
  transition: transform var(--dur) var(--ease), border-color var(--dur) var(--ease);
}

.card:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.12);
}

.card-label {
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 0.65rem;
}

/* ── Color utilities ── */
.up   { color: var(--up); }
.down { color: var(--down); }

/* ── Number typography ── */
.num-xl {
  font-size: clamp(1.4rem, 2.5vw, 1.9rem);
  font-weight: 700;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
}

.num-lg {
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}

.num-sm {
  font-size: 0.76rem;
  font-variant-numeric: tabular-nums;
}

/* ── Bento layout ── */
.bento { display: flex; flex-direction: column; gap: 0.85rem; }

.grid-5 {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.75rem;
}

.grid-2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.grid-2x2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.grid-portfolio-row {
  display: grid;
  grid-template-columns: 1.7fr 1fr;
  gap: 0.75rem;
  align-items: start;
}

/* ── Index card ── */
.index-name {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--muted);
  margin-bottom: 0.4rem;
}

/* ── Portfolio summary ── */
.pf-total-row {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 0.3rem;
}

.pf-badge {
  font-size: 0.76rem;
  font-weight: 600;
  padding: 0.18rem 0.55rem;
  border-radius: 2rem;
}

.pf-badge.up   { background: rgba(16, 185, 129, 0.12); color: var(--up); }
.pf-badge.down { background: rgba(244, 63, 94, 0.12);  color: var(--down); }

/* ── Holding card ── */
.holding-ticker { font-size: 0.76rem; font-weight: 700; color: #a5b4fc; }
.holding-name   { font-size: 0.68rem; color: var(--muted); margin-top: 0.1rem; }
.holding-entry  { font-size: 0.68rem; color: var(--muted); margin-top: 0.4rem; }

/* ── Chart containers ── */
.chart-h300 { position: relative; height: 280px; }
.chart-h180 { position: relative; height: 160px; }

/* ── News ── */
.news-section-title {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.75rem;
}

.news-list { list-style: none; display: flex; flex-direction: column; gap: 0.55rem; }

.news-item {
  display: flex;
  gap: 0.45rem;
  font-size: 0.76rem;
  line-height: 1.4;
  color: #94a3b8;
}

.news-num { color: var(--muted); flex-shrink: 0; }

/* ── Portfolio news grid ── */
.pf-news-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(195px, 1fr));
  gap: 0.75rem;
  margin-top: 0.75rem;
}

.pf-news-ticker {
  font-size: 0.7rem;
  font-weight: 700;
  color: #a5b4fc;
  margin-bottom: 0.5rem;
}

.pf-news-item {
  font-size: 0.72rem;
  color: #64748b;
  line-height: 1.4;
  padding: 0.3rem 0;
  border-top: 1px solid var(--border);
}

/* ── Responsive ── */
@media (max-width: 900px) {
  .grid-5 { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 640px) {
  .grid-5              { grid-template-columns: repeat(2, 1fr); }
  .grid-2x2            { grid-template-columns: 1fr; }
  .grid-portfolio-row  { grid-template-columns: 1fr; }
  .header              { flex-direction: column; align-items: flex-start; gap: 0.5rem; }
  .wrapper             { padding: 1rem 0.85rem 3rem; }
}
```

- [ ] **Step 2: `docs/index.html` 전체 교체**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Daily Briefing</title>
  <link rel="stylesheet" href="style.css">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js" defer></script>
  <script src="app.js" defer></script>
</head>
<body>
  <div class="wrapper">

    <header class="header">
      <div>
        <h1 class="title">Daily Briefing</h1>
        <p id="date-label" class="subtitle">로딩 중…</p>
      </div>
      <span class="badge">매일 10:00 KST 자동 업데이트</span>
    </header>

    <main class="bento">

      <!-- ① 지수 카드 5개 -->
      <div class="grid-5" id="stock-cards"></div>

      <!-- ② 포트폴리오 요약 + 환율 -->
      <div class="grid-portfolio-row">
        <div class="card" id="portfolio-total"></div>
        <div class="grid-2">
          <div class="card" id="fx-usd"></div>
          <div class="card" id="fx-jpy"></div>
        </div>
      </div>

      <!-- ③ 포트폴리오 90일 수익률 -->
      <div class="card">
        <p class="card-label">💼 포트폴리오 수익률 추이 (90일)</p>
        <div class="chart-h300"><canvas id="chart-portfolio"></canvas></div>
      </div>

      <!-- ④ 종목별 카드 -->
      <div class="grid-5" id="holdings-cards"></div>

      <!-- ⑤ 지수 추세 차트 2×2 -->
      <div class="grid-2x2">
        <div class="card">
          <p class="card-label">KOSPI</p>
          <div class="chart-h180"><canvas id="chart-KOSPI"></canvas></div>
        </div>
        <div class="card">
          <p class="card-label">S&amp;P 500</p>
          <div class="chart-h180"><canvas id="chart-SP500"></canvas></div>
        </div>
        <div class="card">
          <p class="card-label">NASDAQ</p>
          <div class="chart-h180"><canvas id="chart-NASDAQ"></canvas></div>
        </div>
        <div class="card">
          <p class="card-label">USD / KRW</p>
          <div class="chart-h180"><canvas id="chart-USD"></canvas></div>
        </div>
      </div>

      <!-- ⑥ 뉴스 2×2 -->
      <div class="grid-2x2">
        <div class="card">
          <p class="news-section-title">📰 국내 경제</p>
          <ul id="news-economy" class="news-list"></ul>
        </div>
        <div class="card">
          <p class="news-section-title">🏠 부동산</p>
          <ul id="news-realestate" class="news-list"></ul>
        </div>
        <div class="card">
          <p class="news-section-title">🌍 글로벌</p>
          <ul id="news-global" class="news-list"></ul>
        </div>
        <div class="card">
          <p class="news-section-title">🇺🇸 미국 · 달러</p>
          <ul id="news-usnews" class="news-list"></ul>
        </div>
      </div>

      <!-- ⑦ 종목별 뉴스 -->
      <div class="card">
        <p class="news-section-title">📰 종목별 뉴스</p>
        <div id="portfolio-news-grid" class="pf-news-grid"></div>
      </div>

    </main>
  </div>
</body>
</html>
```

- [ ] **Step 3: 셸 브라우저 확인**

```bash
cd "C:\Users\지니\OneDrive\Desktop\code\2026_0620_kakao-briefing\docs"
python -m http.server 8080
```

`http://localhost:8080` 열기.

기대 결과: 진한 남색 배경(`#070d1a`), 보라 그라디언트 제목 "Daily Briefing", 빈 카드 영역 윤곽 표시 (JS 없으므로 데이터 없음).

- [ ] **Step 4: 커밋**

```bash
git add docs/index.html docs/style.css
git commit -m "feat: 대시보드 HTML 셸 + CSS 디자인 시스템"
```

---

### Task 3: app.js — 데이터 로더 + 지수·환율·포트폴리오 카드

**Files:**
- Create: `docs/app.js`

**Interfaces:**
- Consumes: `data.json` → `{date, stocks, fx, portfolio}` 구조
- Produces: `renderStocks`, `renderFx`, `renderPortfolioSummary`, `renderHoldings` (같은 파일 내 함수)

- [ ] **Step 1: `docs/app.js` 생성**

```javascript
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

/* ── 메인 (Charts & News는 아래 Task에서 추가) ── */
async function main() {
  const data = await fetch("data.json").then(r => r.json());
  if (!data.length) return;

  const latest = data[data.length - 1];
  document.getElementById("date-label").textContent = latest.date + " 기준";

  renderStocks(latest);
  renderFx(latest);
  renderPortfolioSummary(latest);
  renderHoldings(latest);
}

main().catch(console.error);
```

- [ ] **Step 2: 브라우저 확인**

`http://localhost:8080` 새로고침.

기대 결과:
- KOSPI·KOSDAQ·S&P 500·NASDAQ·다우 5개 카드 실제 수치 + 색상(초록/빨강)
- USD/KRW·JPY/KRW 환율 카드
- 포트폴리오 총 평가액 + 손익 배지
- 보유 종목 가치 순으로 정렬된 카드 5개

- [ ] **Step 3: 커밋**

```bash
git add docs/app.js
git commit -m "feat: 지수·환율·포트폴리오 카드 렌더링"
```

---

### Task 4: app.js — 차트 (포트폴리오 90일 + 지수 추세 4개)

**Files:**
- Modify: `docs/app.js`

**Interfaces:**
- Consumes: `data` (전체 배열, 90일 history)
- Produces: `chart-portfolio`, `chart-KOSPI`, `chart-SP500`, `chart-NASDAQ`, `chart-USD` canvas 채움

- [ ] **Step 1: 차트 함수들을 `main()` 위에 추가**

`async function main()` 바로 위에 아래 코드를 삽입:

```javascript
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
      plugins: { legend: { display: false }, tooltip: TOOLTIP },
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
      plugins: { legend: { display: false }, tooltip: TOOLTIP },
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
```

- [ ] **Step 2: `main()` 내 마지막 줄에 차트 호출 추가**

`renderHoldings(latest);` 다음 줄에 추가:

```javascript
  renderPortfolioChart(data);
  renderIndexCharts(data);
```

- [ ] **Step 3: 브라우저 확인**

`http://localhost:8080` 새로고침.

기대 결과:
- 포트폴리오 수익률 라인 차트 (초록/빨강, 현재는 1일치라 짧은 선)
- KOSPI·S&P500·NASDAQ·USD/KRW 추세 차트 4개
- 마우스 호버 시 어두운 배경 툴팁

- [ ] **Step 4: 커밋**

```bash
git add docs/app.js
git commit -m "feat: 포트폴리오 90일 수익률 차트 + 지수 추세 차트"
```

---

### Task 5: app.js — 뉴스 + 종목별 뉴스 + 배포

**Files:**
- Modify: `docs/app.js`

**Interfaces:**
- Consumes: `latest.news.{economy, realestate, global, usnews}` — 각 항목이 `{title, desc}` 객체
- Consumes: `latest.portfolio_news` — `{ticker: {name, items: [{title, desc}]}}`

- [ ] **Step 1: 뉴스 렌더 함수 추가** (`renderPortfolioChart` 위에 삽입)

```javascript
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
```

- [ ] **Step 2: `main()` 내 마지막에 호출 추가**

`renderIndexCharts(data);` 다음:

```javascript
  renderNews(latest);
  renderPortfolioNews(latest);
```

- [ ] **Step 3: 전체 최종 브라우저 확인**

`http://localhost:8080` 새로고침 후 스크롤 전체 확인:

- [ ] 헤더 날짜가 오늘 날짜(`2026-06-21 기준`)로 표시되는가
- [ ] 지수 5개 카드에 실제 수치·색상 표시되는가
- [ ] 포트폴리오 총 평가액·손익 배지 표시되는가
- [ ] 환율 2개 카드 표시되는가
- [ ] 종목 카드 5개 가치 순 정렬되는가
- [ ] 포트폴리오 수익률 차트 렌더링되는가
- [ ] 지수 추세 차트 4개 렌더링되는가
- [ ] 뉴스 4개 섹션에 기사 목록 있는가
- [ ] 모바일(브라우저 너비 375px)에서 레이아웃 깨지지 않는가

- [ ] **Step 4: 커밋 & 푸시**

```bash
git add docs/app.js
git commit -m "feat: 뉴스 섹션 + 종목별 뉴스 렌더링 — 대시보드 완성"
git push
```

- [ ] **Step 5: GitHub Pages 활성화**

GitHub 레포 → Settings → Pages → **Branch: main / Folder: /docs** → Save.

약 1분 후 `https://hyunjin4459-coder.github.io/daily-briefing/` 에서 대시보드 확인.

---

## Self-Review

**Spec coverage:**
- ✅ GitHub Pages `/docs` 폴더 사용
- ✅ 완전 정적 (fetch + JS만)
- ✅ 다크모드 (`#070d1a` 배경)
- ✅ 벤토 그리드 레이아웃
- ✅ 90일 포트폴리오 수익률 라인 차트
- ✅ 지수·환율 카드
- ✅ 종목별 현황 카드
- ✅ 뉴스 4개 섹션 + 종목별 뉴스
- ✅ Chart.js 4.4 CDN (TailwindCSS CDN 대신 CSS Custom Properties 사용)

**Placeholder scan:** 없음 — 모든 스텝에 실제 코드 포함.

**Type consistency:**
- `data[n].portfolio.holdings[i]` → `{ticker, name, avg_price, current_price, value, pnl_pct}` 일관
- `data[n].portfolio_news[ticker]` → `{name, items: [{title, desc}]}` 일관
- 모든 `id` 속성이 HTML(Task 2) ↔ JS(Task 3-5) 간 일치
