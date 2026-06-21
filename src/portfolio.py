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


def _get_price(symbol: str) -> float | None:
    try:
        resp = _SESSION.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
            params={"interval": "1d", "range": "5d"},
            timeout=15,
        )
        resp.raise_for_status()
        closes = resp.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        closes = [c for c in closes if c is not None]
        return round(closes[-1], 4) if closes else None
    except Exception as e:
        print(f"⚠️ {symbol} 가격 조회 실패: {e}")
        return None


def get_portfolio() -> dict:
    if not _PORTFOLIO_FILE.exists():
        return {"holdings": [], "total_value": 0.0, "total_cost": 0.0, "total_pnl": 0.0, "total_pnl_pct": 0.0}

    config = json.loads(_PORTFOLIO_FILE.read_text(encoding="utf-8"))
    holdings = []
    total_value = 0.0
    total_cost = 0.0

    for h in config.get("holdings", []):
        price = _get_price(h["ticker"])
        if price is None:
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
