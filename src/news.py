import html
import re
import feedparser

_BASE    = "https://news.google.com/rss/search?hl=ko&gl=KR&ceid=KR:ko&q={q}"
_BASE_EN = "https://news.google.com/rss/search?hl=en&gl=US&ceid=US:en&q={q}"


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


def _fetch_en(query: str, count: int = 2) -> list[dict]:
    feed = feedparser.parse(_BASE_EN.format(q=query))
    results = []
    for e in feed.entries[:count]:
        title = _clean_title(e.title)
        desc = _clean_desc(getattr(e, "summary", ""))
        if desc == title:
            desc = ""
        results.append({"title": title, "desc": desc[:250] if desc else ""})
    return results


_TICKER_KO = {
    "JOBY":  "조비에비에이션+주가+전망",
    "QQQ":   "QQQ+ETF+나스닥",
    "GOOGL": "알파벳+구글+주가+전망",
    "BLDR":  "빌더스퍼스트소스+BLDR+주가",
    "NOW":   "서비스나우+NOW+주가",
}


def get_portfolio_news(holdings: list[dict]) -> dict:
    """보유 종목별 최신 뉴스 2건씩 조회 (한글 우선)"""
    result = {}
    for h in holdings:
        ticker = h["ticker"]
        query = _TICKER_KO.get(ticker, f"{ticker}+주가")
        items = _fetch(query, count=2)
        if not items:
            items = _fetch_en(f"{ticker}+stock", count=2)
        if items:
            result[ticker] = {"name": h["name"], "items": items}
    return result


def get_news() -> dict:
    return {
        "economy":    _fetch("한국+경제+금리+증시"),
        "realestate": _fetch("부동산+아파트+가격"),
        "global":     _fetch("글로벌+경제+미국+유럽+중국+지정학"),
        "usnews":     _fetch("미국+연준+달러+국제유가+에너지"),
    }
