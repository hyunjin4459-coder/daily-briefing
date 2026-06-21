import os
import json
import anthropic


def _client():
    return anthropic.Anthropic()


def _fmt_news(items: list[dict], limit: int = 5) -> str:
    return "\n".join(f"- {it['title']}" for it in items[:limit])


def _parse_json(raw: str) -> dict:
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return {}


def generate_signal(news: dict, stocks: dict, sectors: list[dict]) -> dict:
    """분석가 → 비평가 2단계 AI 시장 신호 생성"""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return {
            "signal": "HOLD", "score": 50,
            "reason": "API 키 없음 — GitHub Actions에서 실행 시 생성됩니다",
            "top_risk": "", "critique": "",
            "analyst_signal": "HOLD", "analyst_score": 50,
        }

    sp500 = stocks.get("SP500", {})
    kospi = stocks.get("KOSPI", {})
    top3 = [f"{s['name']}({s['pct']:+.1f}%)" for s in sectors[:3]] if sectors else []
    bot3 = [f"{s['name']}({s['pct']:+.1f}%)" for s in sectors[-3:]] if len(sectors) >= 3 else []

    context = f"""오늘의 시장 현황:
- S&P 500: {sp500.get('close', 'N/A')} ({sp500.get('pct', 0):+.2f}%)
- KOSPI: {kospi.get('close', 'N/A')} ({kospi.get('pct', 0):+.2f}%)
- 강세 섹터: {', '.join(top3) if top3 else 'N/A'}
- 약세 섹터: {', '.join(bot3) if bot3 else 'N/A'}

주요 뉴스:
{_fmt_news(news.get('economy', []))}
{_fmt_news(news.get('global', []))}
{_fmt_news(news.get('usnews', []))}"""

    analyst_prompt = f"""{context}

위 정보를 바탕으로 오늘의 투자 시그널을 분석하세요.
반드시 JSON 형식으로만 답하세요 (마크다운 없이):
{{"signal":"BUY 또는 HOLD 또는 SELL","score":0~100,"reason":"핵심 근거 2-3문장","top_risk":"가장 큰 리스크 1문장"}}"""

    client = _client()
    analyst_raw = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": analyst_prompt}],
    ).content[0].text.strip()

    analyst = _parse_json(analyst_raw)
    if not analyst.get("signal"):
        analyst = {"signal": "HOLD", "score": 50, "reason": analyst_raw[:200], "top_risk": ""}

    critic_prompt = f"""아래는 AI 투자 분석가의 시장 분석입니다:
신호: {analyst['signal']} (점수 {analyst['score']}/100)
근거: {analyst.get('reason', '')}
리스크: {analyst.get('top_risk', '')}

당신은 비판적 검토자입니다. 이 분석의 약점이나 간과한 요소를 1-2문장으로 지적하고, 최종 신호와 조정된 점수를 반환하세요.
반드시 JSON 형식으로만 (마크다운 없이):
{{"critique":"비판 1-2문장","final_signal":"BUY 또는 HOLD 또는 SELL","final_score":0~100}}"""

    critic_raw = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": critic_prompt}],
    ).content[0].text.strip()

    critic = _parse_json(critic_raw)
    if not critic.get("final_signal"):
        critic = {
            "critique": critic_raw[:200],
            "final_signal": analyst["signal"],
            "final_score": analyst["score"],
        }

    return {
        "signal": critic.get("final_signal", analyst["signal"]),
        "score": critic.get("final_score", analyst["score"]),
        "reason": analyst.get("reason", ""),
        "top_risk": analyst.get("top_risk", ""),
        "critique": critic.get("critique", ""),
        "analyst_signal": analyst["signal"],
        "analyst_score": analyst["score"],
    }
