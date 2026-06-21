import json
import os
import datetime
import pathlib

from src.fx import get_exchange_rates
from src.stock import get_stock_data
from src.news import get_news, get_portfolio_news
from src.summary import analyze_all
from src.portfolio import get_portfolio
from src.sector import get_sector_data
from src.signal import generate_signal

DATA_FILE = pathlib.Path(__file__).parent.parent / "docs" / "data.json"
RECO_FILE = pathlib.Path(__file__).parent.parent / "docs" / "recommendations.json"

TRIPLE_TP   =  0.05
TRIPLE_SL   = -0.03
TRIPLE_DAYS =  10


def _update_recommendations(recos: list[dict], sp500_close: float, today: str) -> None:
    for r in recos:
        if r.get("outcome") is not None:
            continue
        entry_price = r["sp500_entry"]
        if not entry_price:
            continue
        ret = (sp500_close - entry_price) / entry_price
        days_held = (
            datetime.date.fromisoformat(today) - datetime.date.fromisoformat(r["date"])
        ).days
        if ret >= TRIPLE_TP:
            r["outcome"] = "WIN"
        elif ret <= TRIPLE_SL:
            r["outcome"] = "LOSS"
        elif days_held >= TRIPLE_DAYS:
            r["outcome"] = "NEUTRAL"
        if r.get("outcome"):
            r["outcome_date"] = today
            r["outcome_return"] = round(ret * 100, 2)
            r["outcome_days"] = days_held


def _add_recommendation(recos: list[dict], signal: dict, sp500_close: float, today: str) -> None:
    if any(r["date"] == today for r in recos):
        return
    recos.append({
        "date": today,
        "signal": signal["signal"],
        "score": signal["score"],
        "sp500_entry": sp500_close,
        "sp500_tp": round(sp500_close * (1 + TRIPLE_TP), 2),
        "sp500_sl": round(sp500_close * (1 + TRIPLE_SL), 2),
        "outcome": None,
        "outcome_date": None,
        "outcome_return": None,
        "outcome_days": None,
    })


def save_data(
    stocks: dict,
    fx: dict,
    news: dict,
    portfolio: dict | None = None,
    portfolio_news: dict | None = None,
    sectors: list | None = None,
    signal: dict | None = None,
    ai_analysis: str | None = None,
) -> None:
    today = datetime.date.today().isoformat()
    entry = {
        "date": today,
        "stocks": stocks,
        "fx": fx,
        "news": news,
        "portfolio": portfolio,
        "portfolio_news": portfolio_news or {},
        "sectors": sectors or [],
        "signal": signal or {},
        "ai_analysis": ai_analysis or "",
    }
    existing = json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else []
    existing = [e for e in existing if e["date"] != today]
    existing.append(entry)
    existing = existing[-365:]
    DATA_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[main] 데이터 저장 완료 ({len(existing)}일치)")


def save_recommendations(recos: list[dict]) -> None:
    RECO_FILE.write_text(json.dumps(recos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[main] 추천 이력 저장 완료 ({len(recos)}건)")


def run():
    from dotenv import load_dotenv
    load_dotenv()

    today = datetime.date.today().isoformat()

    print("[main] 데이터 수집 중...")
    stocks = get_stock_data()
    fx = get_exchange_rates()
    news = get_news()

    print("[main] 포트폴리오 조회 중...")
    portfolio = get_portfolio()

    print("[main] 종목별 뉴스 조회 중...")
    portfolio_news = get_portfolio_news(portfolio.get("holdings", []))

    print("[main] 섹터 데이터 조회 중...")
    sectors = get_sector_data()

    print("[main] AI 시장 신호 생성 중...")
    signal = generate_signal(news, stocks, sectors)

    print("[main] AI 심층 분석 중...")
    ai_analysis = analyze_all(portfolio, portfolio_news, news)

    print("[main] 추천 이력 업데이트 중...")
    recos = json.loads(RECO_FILE.read_text(encoding="utf-8")) if RECO_FILE.exists() else []
    sp500_close = stocks.get("SP500", {}).get("close", 0.0)
    _update_recommendations(recos, sp500_close, today)
    _add_recommendation(recos, signal, sp500_close, today)

    print("[main] 데이터 저장 중...")
    save_data(stocks, fx, news, portfolio, portfolio_news, sectors, signal, ai_analysis)
    save_recommendations(recos)


if __name__ == "__main__":
    run()
