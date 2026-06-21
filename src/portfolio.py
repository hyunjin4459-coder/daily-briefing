import json
import pathlib
import requests

_PORTFOLIO_FILE = pathlib.Path(__file__).parent.parent / "portfolio.json"

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
})


def _get_crumb() -> str | None:
    try:
        r = _SESSION.get("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=5)
        if r.status_code == 200 and r.text:
            return r.text.strip()
    except Exception:
        pass
    return None


def _get_prices(symbols: list[str]) -> dict[str, float]:
    """여러 종목 가격을 한 번에 조회. 실패 시 개별 v8 호출로 폴백."""
    crumb = _get_crumb()
    params: dict = {"symbols": ",".join(symbols), "fields": "regularMarketPrice"}
    if crumb:
        params["crumb"] = crumb
    try:
        resp = _SESSION.get(
            "https://query1.finance.yahoo.com/v7/finance/quote",
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        quotes = resp.json()["quoteResponse"]["result"]
        prices = {q["symbol"]: round(q["regularMarketPrice"], 4) for q in quotes if "regularMarketPrice" in q}
        if prices:
            return prices
    except Exception as e:
        print(f"[portfolio] 배치 조회 실패, 개별 조회로 전환: {e}")

    # 폴백: v8 chart 개별 호출
    prices = {}
    for sym in symbols:
        try:
            r = _SESSION.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}",
                params={"interval": "1d", "range": "5d"},
                timeout=10,
            )
            r.raise_for_status()
            closes = r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
            closes = [c for c in closes if c is not None]
            if closes:
                prices[sym] = round(closes[-1], 4)
        except Exception as e2:
            print(f"[portfolio] {sym} 개별 조회 실패: {e2}")
    return prices


def get_portfolio() -> dict:
    if not _PORTFOLIO_FILE.exists():
        return {"holdings": [], "total_value": 0.0, "total_cost": 0.0, "total_pnl": 0.0, "total_pnl_pct": 0.0}

    config = json.loads(_PORTFOLIO_FILE.read_text(encoding="utf-8"))
    holdings_config = config.get("holdings", [])
    if not holdings_config:
        return {"holdings": [], "total_value": 0.0, "total_cost": 0.0, "total_pnl": 0.0, "total_pnl_pct": 0.0}

    symbols = [h["ticker"] for h in holdings_config]
    prices = _get_prices(symbols)

    holdings = []
    total_value = 0.0
    total_cost = 0.0

    for h in holdings_config:
        price = prices.get(h["ticker"])
        if price is None:
            print(f"[portfolio] {h['ticker']} 가격 없음 (skip)")
            continue
        shares = h["shares"]
        avg_price = h["avg_price"]
        cost = shares * avg_price
        value = shares * price
        pnl = value - cost
        pnl_pct = (pnl / cost) * 100 if cost > 0 else 0.0

        holdings.append({
            "ticker": h["ticker"],
            "name": h["name"],
            "shares": shares,
            "avg_price": avg_price,
            "current_price": price,
            "value": value,
            "cost": cost,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
        })
        total_value += value
        total_cost += cost

    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost) * 100 if total_cost > 0 else 0.0

    return {
        "holdings": holdings,
        "total_value": total_value,
        "total_cost": total_cost,
        "total_pnl": total_pnl,
        "total_pnl_pct": total_pnl_pct,
    }
