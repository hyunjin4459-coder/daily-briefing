import io
import requests
import pandas as pd

STOOQ_SYMBOLS = {
    "KOSPI":  "^kos11",
    "KOSDAQ": "^kq11",
    "SP500":  "^spx",
    "NASDAQ": "^ndq",
    "DOW":    "^dji",
}

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
}


def _get_stooq(name: str, symbol: str) -> dict:
    resp = requests.get(
        f"https://stooq.com/q/d/l/?s={symbol}&i=d",
        headers=_HEADERS,
        timeout=15,
    )
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    df = df.dropna(subset=["Close"]).sort_values("Date")
    if len(df) < 2:
        raise RuntimeError(f"Stooq 데이터 부족: {name} ({symbol})")
    close = round(float(df["Close"].iloc[-1]), 2)
    prev = round(float(df["Close"].iloc[-2]), 2)
    change = round(close - prev, 2)
    pct = round((change / prev) * 100, 2)
    return {"close": close, "change": change, "pct": pct}


def get_stock_data() -> dict:
    return {name: _get_stooq(name, sym) for name, sym in STOOQ_SYMBOLS.items()}
