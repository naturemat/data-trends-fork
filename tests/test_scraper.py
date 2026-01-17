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
    <div class="list-container">
        <ul>
            <li>
                <a class="trend-link">Python AI</a>
            </li>
            <li>
                <a class="trend-link">Scrapy Testing</a>
            </li>
        </ul>
    </div>
    """

    response = fake_response("https://trends24.in/", html)

    items = list(spider.parse(response, country="worldwide"))

    assert len(items) == 2

    assert items[0]["trend"] == "Python AI"
    assert items[0]["country"] == "worldwide"

    assert items[1]["trend"] == "Scrapy Testing"
    assert items[1]["country"] == "worldwide"


def test_parse_country():
    spider = scraper()

    html = """
    <div class="list-container">
        <ul>
            <li>
                <a class="trend-link">Messi</a>
            </li>
            <li>
                <a class="trend-link">River Plate</a>
            </li>
        </ul>
    </div>
    """

    response = fake_response("https://trends24.in/argentina/", html)

    items = list(spider.parse(response, country="argentina"))

    assert len(items) == 2
    assert items[0]["trend"] == "Messi"
    assert items[0]["country"] == "argentina"
    
def test_parse_without_list_container():
    spider = scraper()

    html = "<html><body><p>No trends here</p></body></html>"
    response = fake_response("https://trends24.in/", html)

    items = list(spider.parse(response, country="worldwide"))

    assert items == []
    
def test_parse_removes_duplicates():
    spider = scraper()

    html = """
    <div class="list-container">
        <ul>
            <li><a class="trend-link">Python</a></li>
            <li><a class="trend-link">Python</a></li>
            <li><a class="trend-link">python</a></li>
        </ul>
    </div>
    """

    response = fake_response("https://trends24.in/", html)
    items = list(spider.parse(response, country="worldwide"))

    assert len(items) == 1
    assert items[0]["trend"] == "Python"
    
def test_parse_ignores_empty_trends():
    spider = scraper()

    html = """
    <div class="list-container">
        <ul>
            <li><a class="trend-link"></a></li>
            <li><a></a></li>
            <li></li>
            <li><a class="trend-link">Valid Trend</a></li>
        </ul>
    </div>
    """

    response = fake_response("https://trends24.in/", html)
    items = list(spider.parse(response, country="worldwide"))

    assert len(items) == 1
    assert items[0]["trend"] == "Valid Trend"
    
def test_parse_uses_only_first_list_container():
    spider = scraper()

    html = """
    <div class="list-container">
        <ul>
            <li><a class="trend-link">Current Trend</a></li>
        </ul>
    </div>

    <div class="list-container">
        <ul>
            <li><a class="trend-link">Old Trend</a></li>
        </ul>
    </div>
    """

    response = fake_response("https://trends24.in/", html)
    items = list(spider.parse(response, country="worldwide"))

    assert len(items) == 1
    assert items[0]["trend"] == "Current Trend"
    
def test_country_is_preserved():
    spider = scraper()

    html = """
    <div class="list-container">
        <ul>
            <li><a class="trend-link">Trend EC</a></li>
        </ul>
    </div>
    """

    response = fake_response("https://trends24.in/ecuador/", html)
    items = list(spider.parse(response, country="ecuador"))

    assert items[0]["country"] == "ecuador"

def test_collected_mode_accumulates_data():
    spider = scraper()
    scraper.collected = []

    html = """
    <div class="list-container">
        <ul>
            <li><a class="trend-link">Trend 1</a></li>
            <li><a class="trend-link">Trend 2</a></li>
        </ul>
    </div>
    """

    response = fake_response("https://trends24.in/", html)
    list(spider.parse(response, country="worldwide"))

    assert len(scraper.collected) == 2