import pytest
from scrapy.http import TextResponse, Request
from modules.scraper import scraper


def fake_response(url, html):
    """Crea un TextResponse falso para testear parse()."""
    request = Request(url=url)
    return TextResponse(
        url=url,
        request=request,
        body=html,
        encoding="utf-8"
    )


def test_parse_worldwide():
    spider = scraper()

    html = """
    <ul>
        <li class="trend-card__list-item">
            <a class="trend-link">Python AI</a>
            <span class="tweet-count" data-count="12000"></span>
        </li>

        <li class="trend-card__list-item">
            <a class="trend-link">Scrapy Testing</a>
        </li>
    </ul>
    """

    response = fake_response("https://trends24.in/", html)

    items = list(spider.parse(response, country="worldwide"))

    assert len(items) == 2

    assert items[0]["trend"] == "Python AI"
    assert items[0]["tweet_count"] == 12000
    assert items[0]["country"] == "worldwide"

    assert items[1]["trend"] == "Scrapy Testing"
    assert items[1]["tweet_count"] is None


def test_parse_country():
    spider = scraper()

    html = """
    <ul>
        <li class="bg-sky-50">
            <a class="trend-link">Messi</a>
            <span class="tweet-count" data-count="45000"></span>
        </li>

        <li class="dark:bg-slate-950">
            <a class="trend-link">River Plate</a>
        </li>
    </ul>
    """

    response = fake_response("https://trends24.in/argentina/", html)

    items = list(spider.parse(response, country="argentina"))

    assert len(items) == 2
    assert items[0]["trend"] == "Messi"
    assert items[0]["country"] == "argentina"