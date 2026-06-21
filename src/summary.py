import os
import datetime
import anthropic


def _client():
    return anthropic.Anthropic()


def _fmt_news(items: list[dict]) -> str:
    return "\n".join(f"- {it['title']}" for it in items)


def analyze_all(portfolio: dict, portfolio_news: dict, news: dict) -> str:
    """두 번째 메시지: 종목별 + 뉴스별 영향성 분석 및 향후 전망"""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return ""

    # 보유 종목 + 종목별 뉴스 포맷
    stocks_text = ""
    for h in portfolio.get("holdings", []):
        ticker = h["ticker"]
        arr = "▲" if h["pnl_pct"] >= 0 else "▼"
        stocks_text += f"\n[{ticker}] {h['name']} 진입 ${h['avg_price']:.2f} → 현재 ${h['current_price']:.2f} ({arr}{abs(h['pnl_pct']):.1f}%)\n"
        if ticker in portfolio_news:
            for item in portfolio_news[ticker]["items"]:
                stocks_text += f"  - {item['title']}\n"

    prompt = f"""당신은 한국 경제·투자 전문 애널리스트입니다. 마크다운 헤더(#)는 절대 사용하지 마세요.

## 보유 종목 현황 및 관련 뉴스
{stocks_text}

## 오늘 주요 뉴스
[한국 경제]
{_fmt_news(news.get('economy', []))}

[글로벌/미국]
{_fmt_news(news.get('global', []))}
{_fmt_news(news.get('usnews', []))}

다음 두 섹션을 작성하세요:

섹션1 - 보유 종목별 분석 (각 종목마다):
[티커] 종목명
→ 현황: (최근 상황 1-2문장)
→ 향후 전망: (1-2문장)
→ 내 포지션: (보유 판단 1문장)

섹션2 - 오늘 뉴스 중 내 투자에 영향 큰 것 5개:
① [뉴스 제목]
→ 무슨 일: (1문장)
→ 영향 및 전망: (1-2문장)
"""

    today = datetime.date.today().strftime("%Y-%m-%d")
    msg = _client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    body = msg.content[0].text.strip()
    return f"🤖 AI 심층 분석 [{today}]\n\n{body}"
