import pandas as pd
from unittest.mock import patch, MagicMock
from src.stock import get_stock_data


def _make_stooq_csv(rows: list[tuple]) -> str:
    lines = ["Date,Open,High,Low,Close,Volume"]
    for date, close in rows:
        lines.append(f"{date},0,0,0,{close},0")
    return "\n".join(lines)


def _mock_get(csv_text):
    mock = MagicMock()
    mock.status_code = 200
    mock.text = csv_text
    mock.raise_for_status = MagicMock()
    return mock


CSV_5_ROWS = _make_stooq_csv([
    ("2026-06-18", 2637.84),
    ("2026-06-19", 2650.34),
])


def test_get_stock_data_returns_all_keys():
    with patch("src.stock.requests.get", return_value=_mock_get(CSV_5_ROWS)):
        data = get_stock_data()

    assert set(data.keys()) == {"KOSPI", "KOSDAQ", "SP500", "NASDAQ", "DOW"}
    for key in data:
        assert "close" in data[key]
        assert "change" in data[key]
        assert "pct" in data[key]


def test_change_calculation():
    with patch("src.stock.requests.get", return_value=_mock_get(CSV_5_ROWS)):
        data = get_stock_data()

    assert data["KOSPI"]["close"] == 2650.34
    assert abs(data["KOSPI"]["change"] - 12.5) < 0.01
    assert abs(data["KOSPI"]["pct"] - 0.47) < 0.01
