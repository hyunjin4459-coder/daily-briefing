import json
from unittest.mock import patch, MagicMock
from src.stock import get_stock_data


def _naver_resp(close, change, pct):
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.json.return_value = {
        "closePrice": str(close),
        "compareToPreviousClosePrice": str(change),
        "fluctuationsRatio": str(pct),
    }
    return mock


def _yahoo_resp(closes):
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.json.return_value = {
        "chart": {
            "result": [{
                "indicators": {
                    "quote": [{"close": closes}]
                }
            }]
        }
    }
    return mock


def _make_get_side_effect():
    naver_kospi  = _naver_resp(2650.34, 12.50, 0.47)
    naver_kosdaq = _naver_resp(870.21, -3.10, -0.35)
    yahoo_sp500  = _yahoo_resp([5273.70, 5302.10])
    yahoo_nasdaq = _yahoo_resp([16600.0, 16800.0])
    yahoo_dow    = _yahoo_resp([38000.0, 38200.0])

    def side_effect(url, **kwargs):
        if "KOSPI" in url:
            return naver_kospi
        if "KOSDAQ" in url:
            return naver_kosdaq
        if "GSPC" in url:
            return yahoo_sp500
        if "IXIC" in url:
            return yahoo_nasdaq
        if "DJI" in url:
            return yahoo_dow
        raise ValueError(f"Unexpected URL: {url}")

    return side_effect


def test_get_stock_data_returns_all_keys():
    with patch("src.stock._SESSION.get", side_effect=_make_get_side_effect()):
        data = get_stock_data()

    assert set(data.keys()) == {"KOSPI", "KOSDAQ", "SP500", "NASDAQ", "DOW"}
    for key in data:
        assert "close" in data[key]
        assert "change" in data[key]
        assert "pct" in data[key]


def test_kospi_values():
    with patch("src.stock._SESSION.get", side_effect=_make_get_side_effect()):
        data = get_stock_data()

    assert data["KOSPI"]["close"] == 2650.34
    assert data["KOSPI"]["change"] == 12.50
    assert data["KOSPI"]["pct"] == 0.47
