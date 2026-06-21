"""
1년치 주가 + 환율 데이터를 Yahoo Finance에서 긁어 docs/data.json에 백필.
기존 날짜(오늘 등)는 news/portfolio 유지하고 stocks/fx만 덮어씌우지 않음.

실행: python scripts/backfill_history.py
"""
import json
import time
import pathlib
import datetime
import requests

DATA_FILE = pathlib.Path(__file__).parent.parent / "docs" / "data.json"

YAHOO_SYMBOLS = {
    "KOSPI":  "^KS11",
    "KOSDAQ": "^KQ11",
    "SP500":  "^GSPC",
    "NASDAQ": "^IXIC",
    "DOW":    "^DJI",
}

FX_SYMBOLS = {
    "USD_KRW": "USDKRW=X",
    "JPY_KRW": "JPYKRW=X",
}

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
})


def fetch_history(symbol: str, period: str = "1y") -> dict[str, float]:
    """Yahoo Finance에서 날짜별 종가 반환 {YYYY-MM-DD: close}"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    resp = SESSION.get(url, params={"interval": "1d", "range": period}, timeout=20)
    resp.raise_for_status()
    result = resp.json()["chart"]["result"][0]
    timestamps = result["timestamp"]
    closes = result["indicators"]["quote"][0]["close"]
    out = {}
    for ts, c in zip(timestamps, closes):
        if c is None:
            continue
        date = datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
        out[date] = round(c, 4)
    return out


def build_stock_row(date: str, prev_closes: dict[str, float], closes: dict[str, float]) -> dict:
    row = {}
    for name, symbol in YAHOO_SYMBOLS.items():
        c = closes[symbol].get(date)
        if c is None:
            continue
        # 전일 종가 찾기 (날짜 기준 정렬된 키에서 date 이전 마지막 값)
        prev = prev_closes[symbol].get(date)
        if prev is None:
            change, pct = 0.0, 0.0
        else:
            change = round(c - prev, 2)
            pct = round((change / prev) * 100, 2)
        row[name] = {"close": round(c, 2), "change": change, "pct": pct}
    return row


def build_fx_row(date: str, fx_data: dict[str, dict[str, float]]) -> dict:
    row = {}
    for key, symbol in FX_SYMBOLS.items():
        v = fx_data[symbol].get(date)
        if v is not None:
            row[key] = round(v, 6)
    return row


def main():
    print("Yahoo Finance에서 1년치 데이터 수집 중...")

    # 종가 데이터 수집
    closes: dict[str, dict[str, float]] = {}
    for name, symbol in YAHOO_SYMBOLS.items():
        print(f"  [{name}] {symbol} ...")
        closes[symbol] = fetch_history(symbol)
        time.sleep(0.5)

    fx_data: dict[str, dict[str, float]] = {}
    for key, symbol in FX_SYMBOLS.items():
        print(f"  [{key}] {symbol} ...")
        fx_data[symbol] = fetch_history(symbol)
        time.sleep(0.5)

    # 전일 종가 맵 생성 (change/pct 계산용)
    prev_closes: dict[str, dict[str, float]] = {}
    for symbol, daily in closes.items():
        sorted_dates = sorted(daily.keys())
        prev_map = {}
        for i, d in enumerate(sorted_dates):
            if i > 0:
                prev_map[d] = daily[sorted_dates[i - 1]]
        prev_closes[symbol] = prev_map

    # 모든 날짜 수집
    all_dates = set()
    for daily in closes.values():
        all_dates.update(daily.keys())
    all_dates = sorted(all_dates)

    # 기존 data.json 로드
    existing: list[dict] = []
    if DATA_FILE.exists():
        existing = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    existing_map = {e["date"]: e for e in existing}

    # 백필 엔트리 생성
    new_entries: list[dict] = []
    skipped = 0
    for date in all_dates:
        if date in existing_map:
            # 이미 있는 날짜는 그대로 유지
            new_entries.append(existing_map[date])
            skipped += 1
            continue

        stocks = build_stock_row(date, prev_closes, closes)
        fx = build_fx_row(date, fx_data)

        if not stocks or not fx:
            continue

        new_entries.append({
            "date": date,
            "stocks": stocks,
            "fx": fx,
            "news": {},
            "portfolio": None,
            "portfolio_news": {},
        })

    # Yahoo Finance 날짜 범위 밖에 있는 기존 엔트리도 보존 (예: 장 휴장일에 수집된 당일 데이터)
    backfilled_dates = {e["date"] for e in new_entries}
    for date, entry in existing_map.items():
        if date not in backfilled_dates:
            new_entries.append(entry)
            skipped += 1

    # 90일 → 365일로 확장 (1년치 보관)
    new_entries = sorted(new_entries, key=lambda e: e["date"])
    new_entries = new_entries[-365:]

    DATA_FILE.write_text(json.dumps(new_entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n완료! 총 {len(new_entries)}일치 저장 (기존 유지 {skipped}일, 신규 {len(new_entries) - skipped}일)")
    print(f"기간: {new_entries[0]['date']} ~ {new_entries[-1]['date']}")


if __name__ == "__main__":
    main()
