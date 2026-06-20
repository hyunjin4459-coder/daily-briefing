from unittest.mock import patch, MagicMock
from src.main import format_message, run


SAMPLE_STOCKS = {
    "KOSPI":  {"close": 2650.34, "change": 12.50,  "pct": 0.47},
    "KOSDAQ": {"close": 870.21,  "change": -3.10,  "pct": -0.35},
    "SP500":  {"close": 5302.10, "change": 28.40,  "pct": 0.54},
    "NASDAQ": {"close": 16742.5, "change": 95.20,  "pct": 0.57},
    "DOW":    {"close": 38921.3, "change": 110.50, "pct": 0.28},
}
SAMPLE_FX = {"USD_KRW": 1382.5, "JPY_KRW": 9.21}
SAMPLE_NEWS = {
    "economy": ["뉴스1", "뉴스2", "뉴스3"],
    "realestate": ["부동산1", "부동산2", "부동산3"],
}


def test_format_message_contains_all_sections():
    msg = format_message(SAMPLE_STOCKS, SAMPLE_FX, SAMPLE_NEWS)
    assert "KOSPI" in msg
    assert "KOSDAQ" in msg
    assert "S&P" in msg
    assert "NASDAQ" in msg
    assert "USD" in msg
    assert "JPY" in msg
    assert "뉴스1" in msg
    assert "부동산1" in msg


def test_format_message_shows_arrow_up_for_positive():
    msg = format_message(SAMPLE_STOCKS, SAMPLE_FX, SAMPLE_NEWS)
    # KOSPI change=+12.50, KOSDAQ change=-3.10
    assert "▲" in msg
    assert "▼" in msg


def test_run_calls_send_message(monkeypatch):
    monkeypatch.setenv("KAKAO_REST_API_KEY", "test_key")
    monkeypatch.setenv("KAKAO_REFRESH_TOKEN", "test_refresh")

    with patch("src.main.get_stock_data", return_value=SAMPLE_STOCKS), \
         patch("src.main.get_exchange_rates", return_value=SAMPLE_FX), \
         patch("src.main.get_news", return_value=SAMPLE_NEWS), \
         patch("src.main.refresh_access_token", return_value="new_access_token"), \
         patch("src.main.send_message") as mock_send:
        run()

    mock_send.assert_called_once()
    sent_text = mock_send.call_args[0][1]
    assert "KOSPI" in sent_text
