from unittest.mock import patch, MagicMock
from src.news import get_news


def _make_feed(titles):
    feed = MagicMock()
    feed.entries = [MagicMock(title=t) for t in titles]
    return feed


def test_get_news_returns_economy_and_realestate():
    economy_feed = _make_feed(["경제뉴스1", "경제뉴스2", "경제뉴스3", "경제뉴스4"])
    realestate_feed = _make_feed(["부동산뉴스1", "부동산뉴스2", "부동산뉴스3"])

    with patch("src.news.feedparser.parse", side_effect=[economy_feed, realestate_feed]):
        result = get_news()

    assert "economy" in result
    assert "realestate" in result
    assert len(result["economy"]) == 3
    assert len(result["realestate"]) == 3
    assert result["economy"][0] == "경제뉴스1"


def test_get_news_handles_empty_feed():
    empty_feed = _make_feed([])

    with patch("src.news.feedparser.parse", side_effect=[empty_feed, empty_feed]):
        result = get_news()

    assert result["economy"] == []
    assert result["realestate"] == []
