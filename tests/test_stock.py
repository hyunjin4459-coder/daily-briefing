import pandas as pd
from unittest.mock import patch, MagicMock
from src.stock import get_stock_data


def _make_krx_df(close, prev_close):
    """PyKRX get_index_ohlcv_by_date 반환값 모사."""
    return pd.DataFrame(
        {"종가": [close], "전일종가": [prev_close]},
        index=["20260620"],
    )


def _make_yf_history(close, prev_close):
    """yfinance Ticker.history() 반환값 모사."""
    return pd.DataFrame(
        {"Close": [prev_close, close]},
    )


def test_get_stock_data_returns_all_keys():
    krx_patch = patch(
        "src.stock.stock.get_index_ohlcv_by_date",
        side_effect=[
            _make_krx_df(2650.34, 2637.84),   # KOSPI
            _make_krx_df(870.21, 873.31),      # KOSDAQ
        ],
    )
    yf_ticker_mock = MagicMock()
    yf_ticker_mock.history.return_value = _make_yf_history(5302.10, 5273.70)
    yf_patch = patch("src.stock.yf.Ticker", return_value=yf_ticker_mock)

    with krx_patch, yf_patch:
        data = get_stock_data()

    assert set(data.keys()) == {"KOSPI", "KOSDAQ", "SP500", "NASDAQ", "DOW"}
    for key in data:
        assert "close" in data[key]
        assert "change" in data[key]
        assert "pct" in data[key]


def test_kospi_change_calculation():
    krx_patch = patch(
        "src.stock.stock.get_index_ohlcv_by_date",
        side_effect=[
            _make_krx_df(2650.34, 2637.84),
            _make_krx_df(870.21, 873.31),
        ],
    )
    yf_ticker_mock = MagicMock()
    yf_ticker_mock.history.return_value = _make_yf_history(5302.10, 5273.70)
    yf_patch = patch("src.stock.yf.Ticker", return_value=yf_ticker_mock)

    with krx_patch, yf_patch:
        data = get_stock_data()

    assert abs(data["KOSPI"]["change"] - 12.50) < 0.01
    assert abs(data["KOSPI"]["pct"] - 0.47) < 0.01
