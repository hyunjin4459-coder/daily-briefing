import os
import anthropic


def summarize_news(news: dict) -> str:
    """Claude Haiku로 뉴스 헤드라인을 2문장으로 요약한다. API 키 없으면 빈 문자열 반환."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return ""

    economy = "\n".join(f"- {h}" for h in news.get("economy", []))
    realestate = "\n".join(f"- {h}" for h in news.get("realestate", []))

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": (
                "다음 뉴스 헤드라인들을 2문장으로 간결하게 한국어로 요약해주세요.\n\n"
                f"경제 뉴스:\n{economy}\n\n"
                f"부동산 뉴스:\n{realestate}"
            ),
        }],
    )
    return message.content[0].text.strip()
