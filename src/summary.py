import os
import anthropic


def summarize_news(news: dict) -> str:
    """Claude Haiku로 뉴스를 분석해 영향과 의미까지 설명한다. API 키 없으면 빈 문자열 반환."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return ""

    def fmt(items): return "\n".join(f"- {h}" for h in items)

    prompt = f"""다음은 오늘의 주요 뉴스 헤드라인입니다.
단순 요약이 아니라, 각 뉴스가 **한국 경제·주식·부동산·환율에 미치는 영향**을 일반 투자자 관점에서 설명해주세요.

[한국 경제]
{fmt(news.get('economy', []))}

[부동산]
{fmt(news.get('realestate', []))}

[글로벌 이슈]
{fmt(news.get('global', []))}

[미국·달러·에너지]
{fmt(news.get('usnews', []))}

다음 형식으로 작성하세요 (각 항목 1-2문장):
📌 오늘의 핵심: (가장 중요한 뉴스 1개와 그 의미)
📈 증시 영향: (주식시장에 미칠 영향)
🏠 부동산 영향: (부동산 시장에 미칠 영향)
🌍 주목할 해외 이슈: (글로벌 변수 중 가장 주의할 것)"""

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()
