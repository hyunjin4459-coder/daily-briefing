import yfinance as yf

SYMBOLS = {
    "KOSPI":  "^KS11",
    "KOSDAQ": "^KQ11",
    "SP500":  "^GSPC",
    "NASDAQ": "^IXIC",
    "DOW":    "^DJI",
}


def get_stock_data() -> dict:
    """국내외 주요 지수 데이터를 한 번의 요청으로 반환한다."""
    tickers = list(SYMBOLS.values())
    data = yf.download(tickers, period="5d", progress=False, auto_adjust=True)
    close_df = data["Close"]

    result = {}
    for name, symbol in SYMBOLS.items():
        series = close_df[symbol].dropna()
        if len(series) < 2:
            raise RuntimeError(f"yfinance 데이터 부족: {symbol}")
        close = round(float(series.iloc[-1]), 2)
        prev_close = round(float(series.iloc[-2]), 2)
        change = round(close - prev_close, 2)
        pct = round((change / prev_close) * 100, 2)
        result[name] = {"close": close, "change": change, "pct": pct}
    return result
