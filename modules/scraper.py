import time
import json
import re
import logging
from collections import Counter

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Scraper:
    """
    Clase encargada de obtener tendencias de X (Twitter).
    Posee:
      ✔ Headless mode para servidores
      ✔ Anti-detección webdriver
      ✔ Logging profesional
      ✔ Limpieza modular y testeable
    """

    def __init__(self, chromedriver_path, cookies_path=None):
        self.log = logging.getLogger("Scraper")
        self.driver = self._create_driver(chromedriver_path)
        self.cookies_path = cookies_path

        if cookies_path:
            self.load_cookies()

    # ============================================================
    # DRIVER SETUP
    # ============================================================
    def _create_driver(self, chromedriver_path):
        chrome_options = Options()

        # HEADLESS en servidores (Jenkins, EC2, Docker)
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

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

        # Anti-detección webdriver=true
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """}
        )

        self.log.info("Driver inicializado en modo headless.")
        return driver

    # ============================================================
    # MÉTODOS AUXILIARES
    # ============================================================
    def close(self):
        self.log.info("Cerrando driver...")
        self.driver.quit()

    def load_cookies(self):
        self.log.info("Cargando cookies desde archivo...")

        try:
            self.driver.get("https://x.com")
            time.sleep(2)

            with open(self.cookies_path, "r", encoding="utf-8") as f:
                cookies = json.load(f)

            for c in cookies:
                try:
                    self.driver.add_cookie(c)
                except Exception:
                    pass  # cookies inválidas son normales

            self.driver.refresh()
            self.log.info("Cookies cargadas correctamente.")

        except Exception as e:
            self.log.error(f"Error al cargar cookies: {e}")

    # ============================================================
    # SCRAPING PRINCIPAL
    # ============================================================
    def get_trending_topics(self):
        self.log.info("Obteniendo tendencias desde X...")
        self.driver.get("https://x.com/explore/tabs/trending")

        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(3)

        cards = self.driver.find_elements(
            By.XPATH,
            "//div[@data-testid='trend' and not(ancestor::*[@aria-label='Promoted'])]"
        )

        raw_topics = []
        for card in cards:
            extracted = self._extract_topics_from_card(card)
            raw_topics.extend(extracted)

        # Eliminar duplicados manteniendo orden
        final_topics = list(dict.fromkeys(raw_topics))
        self.log.info(f"{len(final_topics)} tendencias válidas obtenidas.")

        return final_topics[:20]

    # ============================================================
    # FUNCIONES PRIVADAS
    # ============================================================
    def _extract_topics_from_card(self, card):
        """Extrae candidatos y filtra basura."""
        text = card.text.strip().lower()

        # descartar anuncios
        if any(w in text for w in ["promoted", "promocionado", "sponsored"]):
            return []

        elems = card.find_elements(By.XPATH, ".//div[@dir='ltr']")
        topics = []

        for e in elems:
            t = e.text.strip()
            lo = t.lower()

            if not t:
                continue

            # filtros
            if (
                "publicaciones" in lo or
                "tendencia" in lo or
                lo.isdigit() or
                re.match(r"^\d+(mil)?$", lo) or
                len(lo) <= 2
            ):
                continue

            topics.append(t)

        return topics

    # ============================================================
    # ANÁLISIS DE PALABRAS
    # ============================================================
    def count_words_in_trends(self, topics):
        self.log.info("Contando palabras en tendencias...")

        text = " ".join(topics).lower()
        text = re.sub(r"[^a-z0-9áéíóúñ#]", " ", text)

        words = text.split()
        return Counter(words).most_common(20)