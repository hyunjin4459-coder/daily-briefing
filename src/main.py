import os
import datetime

from src.fx import get_exchange_rates
from src.stock import get_stock_data
from src.news import get_news
from src.kakao import refresh_access_token, send_message


def _arrow(change: float) -> str:
    return "▲" if change >= 0 else "▼"


def format_message(stocks: dict, fx: dict, news: dict) -> str:
    today = datetime.date.today().strftime("%Y-%m-%d")

    lines = [f"📊 오늘의 시장 브리핑 [{today}]", ""]

    # 국내 증시
    lines.append("📈 국내 증시")
    for name, key in [("KOSPI", "KOSPI"), ("KOSDAQ", "KOSDAQ")]:
        d = stocks[key]
        lines.append(
            f"  {name:<8} {d['close']:>9,.2f}  "
            f"{_arrow(d['change'])} {abs(d['change']):.2f} ({d['pct']:+.2f}%)"
        )

    lines.append("")

    # 미국 증시
    lines.append("🌐 미국 증시 (전일 종가)")
    for name, key in [("S&P 500", "SP500"), ("NASDAQ", "NASDAQ"), ("다우", "DOW")]:
        d = stocks[key]
        lines.append(
            f"  {name:<8} {d['close']:>9,.2f}  "
            f"{_arrow(d['change'])} {abs(d['change']):.2f} ({d['pct']:+.2f}%)"
        )

    lines.append("")

    # 환율
    lines.append("💱 환율")
    lines.append(f"  USD/KRW  {fx['USD_KRW']:,.2f}")
    lines.append(f"  JPY/KRW  {fx['JPY_KRW']:.2f}")

    lines.append("")

    # 경제 뉴스
    lines.append("📰 경제 뉴스")
    for i, headline in enumerate(news["economy"], 1):
        lines.append(f"  {i}. {headline}")

    lines.append("")

    # 부동산 뉴스
    lines.append("🏠 부동산 뉴스")
    for i, headline in enumerate(news["realestate"], 1):
        lines.append(f"  {i}. {headline}")

    return "\n".join(lines)


def run():
    from dotenv import load_dotenv
    load_dotenv()
    rest_api_key = os.environ["KAKAO_REST_API_KEY"]
    refresh_token = os.environ["KAKAO_REFRESH_TOKEN"]

    print("📡 데이터 수집 중...")
    stocks = get_stock_data()
    fx = get_exchange_rates()
    news = get_news()

    print("📝 메시지 포맷 중...")
    message = format_message(stocks, fx, news)

    print("🔑 카카오 토큰 갱신 중...")
    access_token = refresh_access_token(rest_api_key, refresh_token)

    print("📨 카카오톡 발송 중...")
    send_message(access_token, message)
    print("✅ 발송 완료")


if __name__ == "__main__":
    run()
