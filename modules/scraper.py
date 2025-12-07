import time
import json
import re
from collections import Counter

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Scraper:

    @staticmethod
    def create_driver(chromedriver_path):
        chrome_options = Options()

        # MODO HEADLESS PARA SERVIDOR (obligatorio en EC2/Jenkins)
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Evitar detección por parte de X
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--window-size=1920,1080")

        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Evadir detección
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """}
        )

        return driver

    def __init__(self, chromedriver_path, cookies_path=None):
        self.driver = self.create_driver(chromedriver_path)
        self.cookies_path = cookies_path

        if cookies_path:
            self.load_cookies()

    def close(self):
        self.driver.quit()

    # CARGAR COOKIES (SESIÓN DE X)
    def load_cookies(self):
        try:
            print("Cargando cookies...")
            self.driver.get("https://x.com")
            time.sleep(2)

            with open(self.cookies_path, "r", encoding="utf-8") as f:
                cookies = json.load(f)

            for c in cookies:
                try:
                    self.driver.add_cookie(c)
                except Exception:
                    pass  # Algunos cookies pueden fallar, es normal.

            self.driver.refresh()
            time.sleep(2)
            print("Cookies cargadas correctamente.")

        except Exception as e:
            print(f"No se pudieron cargar cookies: {str(e)}")

    # SCRAPEAR TENDENCIAS
    def get_trending_topics(self):
        print("\n→ Obteniendo tendencias de X...")
        self.driver.get("https://x.com/explore/tabs/trending")

        # Espera hasta que el body esté cargado
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(3)

        trend_cards = self.driver.find_elements(
            By.XPATH,
            "//div[@data-testid='trend' and not(ancestor::*[@aria-label='Promoted'])]"
        )

        topics = []

        for card in trend_cards:
            txt = card.text.strip().lower()

            # Filtrar anuncios
            if any(bad in txt for bad in [
                "promoted", "promocionado", "promoted by", "sponsored"
            ]):
                continue

            elems = card.find_elements(By.XPATH, ".//div[@dir='ltr']")

            for e in elems:
                t = e.text.strip()
                lo = t.lower()

                if not t:
                    continue

                # filtros de basura
                if (
                    "publicaciones" in lo or
                    "tendencia" in lo or
                    lo.isdigit() or
                    re.match(r"^\d+(mil)?$", lo) or
                    len(lo) <= 2
                ):
                    continue

                topics.append(t)

        final_topics = list(dict.fromkeys(topics))
        print(f"Tendencias válidas encontradas: {len(final_topics)}")

        return final_topics[:20]

    # ANALIZAR PALABRAS MÁS USADAS
    def count_words_in_trends(self, topics):
        print("\nContando palabras...")

        text = " ".join(topics).lower()
        text = re.sub(r"[^a-z0-9áéíóúñ#]", " ", text)
        words = text.split()

        return Counter(words).most_common(20)