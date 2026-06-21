import requests

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
})

SECTOR_ETFS = {
    "XLK":  "기술",
    "XLF":  "금융",
    "XLE":  "에너지",
    "XLV":  "헬스케어",
    "XLB":  "소재",
    "XLC":  "커뮤니케이션",
    "XLRE": "부동산",
    "XLU":  "유틸리티",
    "XLI":  "산업",
    "XLP":  "필수소비재",
    "XLY":  "임의소비재",
}


def _get_yahoo(symbol: str) -> dict:
    resp = _SESSION.get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
        params={"interval": "1d", "range": "5d"},
        timeout=15,
    )
    resp.raise_for_status()
    closes = resp.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
    closes = [c for c in closes if c is not None]
    if len(closes) < 2:
        raise RuntimeError(f"데이터 부족: {symbol}")
    close = round(closes[-1], 2)
    prev = round(closes[-2], 2)
    pct = round((close - prev) / prev * 100, 2)
    return {"close": close, "pct": pct}


def get_sector_data() -> list[dict]:
    result = []
    for symbol, name in SECTOR_ETFS.items():
        try:
            d = _get_yahoo(symbol)
            result.append({"symbol": symbol, "name": name, "close": d["close"], "pct": d["pct"]})
        except Exception as e:
            print(f"[sector] {symbol} 실패: {e}")
    result.sort(key=lambda x: x["pct"], reverse=True)
    return result
