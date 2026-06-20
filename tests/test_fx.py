import pytest
from unittest.mock import patch, MagicMock
from src.fx import get_exchange_rates


def test_get_exchange_rates_returns_usd_and_jpy():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": "success",
        "rates": {"KRW": 1382.5, "JPY": 150.25},
    }
    mock_response.raise_for_status.return_value = None

    with patch("src.fx.requests.get", return_value=mock_response):
        rates = get_exchange_rates()

    assert "USD_KRW" in rates
    assert "JPY_KRW" in rates
    assert rates["USD_KRW"] == 1382.5
    assert abs(rates["JPY_KRW"] - (1382.5 / 150.25)) < 0.01


def test_get_exchange_rates_raises_on_api_error():
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("API Error")

    with patch("src.fx.requests.get", return_value=mock_response):
        with pytest.raises(Exception):
            get_exchange_rates()
