import feedparser

_BASE_URL = "https://news.google.com/rss/search?hl=ko&gl=KR&ceid=KR:ko&q={query}"


def _fetch_headlines(query: str, count: int = 3) -> list:
    url = _BASE_URL.format(query=query)
    feed = feedparser.parse(url)
    return [e.title for e in feed.entries[:count]]


def get_news() -> dict:
    """경제 뉴스와 부동산 뉴스 헤드라인을 반환한다."""
    return {
        "economy": _fetch_headlines("한국+경제+뉴스"),
        "realestate": _fetch_headlines("부동산+뉴스"),
    }
