import yfinance as yf


def _get_yf_index(symbol: str) -> dict:
    """yfinance로 해외 지수 데이터를 가져온다."""
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="2d")
    if len(hist) < 2:
        hist = ticker.history(period="5d")
    if len(hist) < 2:
        raise RuntimeError(f"yfinance 데이터 부족: {symbol} (rows={len(hist)})")
    close = float(hist["Close"].iloc[-1])
    prev_close = float(hist["Close"].iloc[-2])
    change = round(close - prev_close, 2)
    pct = round((change / prev_close) * 100, 2)
    return {"close": close, "change": change, "pct": pct}


def get_stock_data() -> dict:
    """국내외 주요 지수 데이터를 반환한다."""
    return {
        "KOSPI":  _get_yf_index("^KS11"),
        "KOSDAQ": _get_yf_index("^KQ11"),
        "SP500":  _get_yf_index("^GSPC"),
        "NASDAQ": _get_yf_index("^IXIC"),
        "DOW":    _get_yf_index("^DJI"),
    }
