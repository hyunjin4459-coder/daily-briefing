import requests

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
})

NAVER_INDICES = ["KOSPI", "KOSDAQ"]
YAHOO_SYMBOLS = {
    "SP500":  "^GSPC",
    "NASDAQ": "^IXIC",
    "DOW":    "^DJI",
}


def _get_naver(name: str) -> dict:
    resp = _SESSION.get(
        f"https://m.stock.naver.com/api/index/{name}/basic",
        timeout=10,
    )
    resp.raise_for_status()
    d = resp.json()
    close = round(float(d["closePrice"].replace(",", "")), 2)
    change = round(float(d["compareToPreviousClosePrice"].replace(",", "")), 2)
    pct = round(float(d["fluctuationsRatio"]), 2)
    return {"close": close, "change": change, "pct": pct}


def _get_yahoo(name: str, symbol: str) -> dict:
    resp = _SESSION.get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
        params={"interval": "1d", "range": "5d"},
        timeout=15,
    )
    resp.raise_for_status()
    closes = resp.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
    closes = [c for c in closes if c is not None]
    if len(closes) < 2:
        raise RuntimeError(f"Yahoo 데이터 부족: {name} ({symbol})")
    close = round(closes[-1], 2)
    prev = round(closes[-2], 2)
    change = round(close - prev, 2)
    pct = round((change / prev) * 100, 2)
    return {"close": close, "change": change, "pct": pct}


def get_stock_data() -> dict:
    result = {}
    for name in NAVER_INDICES:
        result[name] = _get_naver(name)
    for name, symbol in YAHOO_SYMBOLS.items():
        result[name] = _get_yahoo(name, symbol)
    return result
