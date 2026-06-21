import html
import re
import feedparser

_BASE = "https://news.google.com/rss/search?hl=ko&gl=KR&ceid=KR:ko&q={q}"


def _clean_title(text: str) -> str:
    text = html.unescape(text)               # &nbsp; &amp; 등 HTML 엔티티 변환
    text = re.sub(r"<[^>]+>", "", text)      # <b> </b> 등 HTML 태그 제거
    text = re.sub(r"\s*-\s*[^-]+$", "", text)  # "- 다음넷", "- 연합뉴스" 등 언론사명 제거
    return text.strip()


def _clean_desc(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _fetch(query: str, count: int = 6) -> list[dict]:
    feed = feedparser.parse(_BASE.format(q=query))
    results = []
    for e in feed.entries[:count]:
        title = _clean_title(e.title)
        desc = _clean_desc(getattr(e, "summary", ""))
        if desc == title:
            desc = ""
        results.append({"title": title, "desc": desc[:250] if desc else ""})
    return results


def get_news() -> dict:
    return {
        "economy":    _fetch("한국+경제+금리+증시"),
        "realestate": _fetch("부동산+아파트+가격"),
        "global":     _fetch("글로벌+경제+미국+유럽+중국+지정학"),
        "usnews":     _fetch("미국+연준+달러+국제유가+에너지"),
    }
