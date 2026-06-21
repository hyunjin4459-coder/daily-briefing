import re
import feedparser

_BASE = "https://news.google.com/rss/search?hl=ko&gl=KR&ceid=KR:ko&q={q}"


def _clean(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _fetch(query: str, count: int = 6) -> list[dict]:
    feed = feedparser.parse(_BASE.format(q=query))
    results = []
    for e in feed.entries[:count]:
        desc = _clean(getattr(e, "summary", ""))
        results.append({
            "title": e.title,
            "desc": desc[:300] if desc and desc != e.title else "",
        })
    return results


def get_news() -> dict:
    return {
        "economy":    _fetch("한국+경제+금리+증시"),
        "realestate": _fetch("부동산+아파트+가격"),
        "global":     _fetch("글로벌+경제+미국+유럽+중국+지정학"),
        "usnews":     _fetch("미국+연준+달러+국제유가+에너지"),
    }
