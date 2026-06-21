import json
import os
import datetime
import pathlib

from src.fx import get_exchange_rates
from src.stock import get_stock_data
from src.news import get_news, get_portfolio_news
from src.summary import analyze_all
from src.portfolio import get_portfolio
from src.telegram_bot import send_message

DATA_FILE = pathlib.Path(__file__).parent.parent / "docs" / "data.json"


def _arrow(change: float) -> str:
    return "▲" if change >= 0 else "▼"


def format_message(stocks: dict, fx: dict, news: dict, portfolio: dict | None = None, portfolio_news: dict | None = None) -> str:
    today = datetime.date.today().strftime("%Y-%m-%d")

    lines = [f"📊 오늘의 시장 브리핑 [{today}]", ""]

    lines.append("📈 국내 증시")
    for name, key in [("KOSPI", "KOSPI"), ("KOSDAQ", "KOSDAQ")]:
        d = stocks[key]
        lines.append(
            f"  {name:<8} {d['close']:>9,.2f}  "
            f"{_arrow(d['change'])} {abs(d['change']):.2f} ({d['pct']:+.2f}%)"
        )

    lines.append("")

    lines.append("🌐 미국 증시 (전일 종가)")
    for name, key in [("S&P 500", "SP500"), ("NASDAQ", "NASDAQ"), ("다우", "DOW")]:
        d = stocks[key]
        lines.append(
            f"  {name:<8} {d['close']:>9,.2f}  "
            f"{_arrow(d['change'])} {abs(d['change']):.2f} ({d['pct']:+.2f}%)"
        )

    lines.append("")

    lines.append("💱 환율")
    lines.append(f"  USD/KRW  {fx['USD_KRW']:,.2f}")
    lines.append(f"  JPY/KRW  {fx['JPY_KRW']:.2f}")

    lines.append("")

    if portfolio and portfolio.get("holdings"):
        pf = portfolio
        arr = "▲" if pf["total_pnl"] >= 0 else "▼"
        lines.append("💼 내 포트폴리오 (토스증권)")
        lines.append(
            f"  총 평가액  ${pf['total_value']:,.2f}"
            f"  {arr} ${abs(pf['total_pnl']):,.2f} ({pf['total_pnl_pct']:+.2f}%)"
        )
        lines.append("")
        for h in sorted(pf["holdings"], key=lambda x: -x["value"]):
            arr_h = "▲" if h["pnl"] >= 0 else "▼"
            lines.append(f"  [{h['ticker']}] {h['name']}")
            lines.append(
                f"    진입 ${h['avg_price']:.2f} → 현재 ${h['current_price']:.2f}"
                f"  {arr_h}{abs(h['pnl_pct']):.1f}%  (${h['value']:,.0f})"
            )
            lines.append("")
        lines.append("─" * 20)
        lines.append("")

    if portfolio_news:
        lines.append("📰 종목별 뉴스")
        lines.append("")
        for ticker, data in portfolio_news.items():
            lines.append(f"  [{ticker}] {data['name']}")
            for i, item in enumerate(data["items"], 1):
                lines.append(f"    {i}. {item['title']}")
            lines.append("")
        lines.append("─" * 20)
        lines.append("")

    def news_section(label: str, items: list):
        lines.append(label)
        for i, h in enumerate(items, 1):
            title = h["title"] if isinstance(h, dict) else h
            lines.append(f"  {i}. {title}")
            lines.append("")

    news_section("📰 국내 경제", news.get("economy", []))
    news_section("🏠 부동산", news.get("realestate", []))
    news_section("🌍 글로벌 이슈", news.get("global", []))
    news_section("🇺🇸 미국·달러·에너지", news.get("usnews", []))

    return "\n".join(lines)


def save_data(stocks: dict, fx: dict, news: dict, portfolio: dict | None = None, portfolio_news: dict | None = None) -> None:
    today = datetime.date.today().isoformat()
    entry = {
        "date": today,
        "stocks": stocks,
        "fx": fx,
        "news": news,
        "portfolio": portfolio,
        "portfolio_news": portfolio_news or {},
    }
    existing = json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else []
    existing = [e for e in existing if e["date"] != today]
    existing.append(entry)
    existing = existing[-90:]
    DATA_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[main] 데이터 저장 완료 ({len(existing)}일치)")


def run():
    from dotenv import load_dotenv
    load_dotenv()
    tg_token = os.environ["TELEGRAM_BOT_TOKEN"]
    tg_chat_id = os.environ["TELEGRAM_CHAT_ID"]

    print("[main] 데이터 수집 중...")
    stocks = get_stock_data()
    fx = get_exchange_rates()
    news = get_news()

    print("[main] 포트폴리오 조회 중...")
    portfolio = get_portfolio()

    print("[main] 종목별 뉴스 조회 중...")
    portfolio_news = get_portfolio_news(portfolio.get("holdings", []))

    print("[main] 메시지 포맷 중...")
    message = format_message(stocks, fx, news, portfolio, portfolio_news)

    print("[main] 대시보드 데이터 저장 중...")
    save_data(stocks, fx, news, portfolio, portfolio_news)

    print("[main] 1번 메시지 발송 중...")
    send_message(tg_token, tg_chat_id, message)
    print("[main] 1번 발송 완료")

    print("[main] AI 심층 분석 중...")
    analysis = analyze_all(portfolio, portfolio_news, news)
    if analysis:
        print("[main] 2번 메시지 발송 중...")
        send_message(tg_token, tg_chat_id, analysis)
        print("[main] 2번 발송 완료")


if __name__ == "__main__":
    run()
