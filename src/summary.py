import os
import anthropic


def summarize_news(news: dict) -> str:
    """오늘 뉴스 중 중요한 것을 골라 맥락·영향까지 설명한다. API 키 없으면 빈 문자열 반환."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return ""

    def fmt(items: list[dict]) -> str:
        lines = []
        for it in items:
            lines.append(f"- {it['title']}")
            if it.get("desc"):
                lines.append(f"  ({it['desc']})")
        return "\n".join(lines)

    prompt = f"""당신은 한국 경제·투자 전문 애널리스트입니다.
아래 오늘의 뉴스 헤드라인과 요약을 보고, 가장 중요한 5개 이슈를 골라서 설명해주세요.

[한국 경제]
{fmt(news.get('economy', []))}

[부동산]
{fmt(news.get('realestate', []))}

[글로벌 이슈]
{fmt(news.get('global', []))}

[미국·달러·에너지]
{fmt(news.get('usnews', []))}

각 이슈마다 다음 형식으로 작성하세요:
① [이슈 제목]
→ 무슨 일인지: (2문장 이내로 상황 설명)
→ 나한테 영향: (주식·부동산·환율·일상 중 해당되는 것에 미치는 영향 1-2문장)

5개 모두 위 형식으로 작성. 번호는 ①②③④⑤ 사용."""

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()
