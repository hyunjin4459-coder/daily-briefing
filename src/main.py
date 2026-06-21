import json
import os
import datetime
import pathlib

from src.fx import get_exchange_rates
from src.stock import get_stock_data
from src.news import get_news
from src.summary import summarize_news
from src.kakao import refresh_access_token, send_message

DATA_FILE = pathlib.Path(__file__).parent.parent / "docs" / "data.json"


def _arrow(change: float) -> str:
    return "▲" if change >= 0 else "▼"


def format_message(stocks: dict, fx: dict, news: dict, summary: str) -> str:
    today = datetime.date.today().strftime("%Y-%m-%d")

    lines = [f"📊 오늘의 시장 브리핑 [{today}]", ""]

    if summary:
        lines.append("🔍 오늘 꼭 알아야 할 뉴스")
        lines.append("")
        lines.append(summary)
        lines.append("")
        lines.append("─" * 20)
        lines.append("")

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

    lines.append("📰 국내 경제")
    for i, h in enumerate(news.get("economy", []), 1):
        lines.append(f"  {i}. {h}")

    lines.append("")

    lines.append("🏠 부동산")
    for i, h in enumerate(news.get("realestate", []), 1):
        lines.append(f"  {i}. {h}")

    lines.append("")

    lines.append("🌍 글로벌 이슈")
    for i, h in enumerate(news.get("global", []), 1):
        lines.append(f"  {i}. {h}")

    lines.append("")

    lines.append("🇺🇸 미국·달러·에너지")
    for i, h in enumerate(news.get("usnews", []), 1):
        lines.append(f"  {i}. {h}")

    return "\n".join(lines)


def save_data(stocks: dict, fx: dict, news: dict, summary: str) -> None:
    today = datetime.date.today().isoformat()
    entry = {
        "date": today,
        "stocks": stocks,
        "fx": fx,
        "news": news,
        "news_summary": summary,
    }
    existing = json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else []
    existing = [e for e in existing if e["date"] != today]  # 오늘 날짜 중복 방지
    existing.append(entry)
    existing = existing[-90:]  # 최대 90일치만 보관
    DATA_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"📁 데이터 저장 완료 ({len(existing)}일치)")


def run():
    from dotenv import load_dotenv
    load_dotenv()
    rest_api_key = os.environ["KAKAO_REST_API_KEY"]
    refresh_token = os.environ["KAKAO_REFRESH_TOKEN"]

    print("📡 데이터 수집 중...")
    stocks = get_stock_data()
    fx = get_exchange_rates()
    news = get_news()

    print("🤖 Claude AI 뉴스 요약 중...")
    summary = summarize_news(news)

    print("📝 메시지 포맷 중...")
    message = format_message(stocks, fx, news, summary)

    print("📁 대시보드 데이터 저장 중...")
    save_data(stocks, fx, news, summary)

    print("🔑 카카오 토큰 갱신 중...")
    access_token = refresh_access_token(rest_api_key, refresh_token)

    print("📨 카카오톡 발송 중...")
    send_message(access_token, message)
    print("✅ 발송 완료")


if __name__ == "__main__":
    run()
