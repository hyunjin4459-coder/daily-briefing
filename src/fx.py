import requests


def get_exchange_rates() -> dict:
    """USD/KRW, JPY/KRW 환율을 반환한다. (API 키 불필요)"""
    response = requests.get(
        "https://open.exchangerate-api.com/v6/latest/USD",
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    rates = data["rates"]
    krw = float(rates["KRW"])
    jpy = float(rates["JPY"])
    return {
        "USD_KRW": krw,
        "JPY_KRW": round(krw / jpy, 2),
    }
