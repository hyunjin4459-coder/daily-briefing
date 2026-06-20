import datetime
import yfinance as yf
from pykrx import stock


def _get_krx_index(ticker_code: str) -> dict:
    """PyKRX로 국내 지수 데이터를 가져온다. 오늘 데이터가 없으면 전일을 반환."""
    today = datetime.date.today()
    for days_back in range(0, 5):
        date = today - datetime.timedelta(days=days_back)
        date_str = date.strftime("%Y%m%d")
        try:
            df = stock.get_index_ohlcv_by_date(date_str, date_str, ticker_code)
        except Exception:
            continue
        if not df.empty:
            close = float(df["종가"].iloc[-1])
            prev_close = float(df["전일종가"].iloc[-1])
            change = round(close - prev_close, 2)
            pct = round((change / prev_close) * 100, 2)
            return {"close": close, "change": change, "pct": pct}
    raise RuntimeError(f"KRX 지수 데이터 없음: {ticker_code}")


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
        "KOSPI":  _get_krx_index("1001"),
        "KOSDAQ": _get_krx_index("2001"),
        "SP500":  _get_yf_index("^GSPC"),
        "NASDAQ": _get_yf_index("^IXIC"),
        "DOW":    _get_yf_index("^DJI"),
    }
