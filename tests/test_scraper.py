from unittest.mock import MagicMock, patch
from modules.scraper import Scraper


@patch("modules.scraper.webdriver.Chrome")
def test_get_trending_topics(mock_browser):
    # Mock del navegador
    mock_driver = MagicMock()
    mock_browser.return_value = mock_driver

    # === Mock de tarjetas ===
    card1 = MagicMock()
    card1.find_elements.return_value = [MagicMock(text="Python IA")]

    card2 = MagicMock()
    card2.find_elements.return_value = [MagicMock(text="Scraping avanzado")]

    card3 = MagicMock()
    card3.find_elements.return_value = [MagicMock(text="DevOps Jenkins")]

    # Esto es lo que devuelve driver.find_elements()
    mock_driver.find_elements.return_value = [card1, card2, card3]

    scraper = Scraper(chromedriver_path="fake_path")
    topics = scraper.get_trending_topics()

    assert len(topics) == 3
    assert topics == ["Python IA", "Scraping avanzado", "DevOps Jenkins"]