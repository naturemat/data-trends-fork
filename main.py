import os
import sys
import logging
from datetime import datetime
import pandas as pd

from modules.scraper import Scraper


# ============================================================
# CONFIG LOGGING
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

log = logging.getLogger("Runner")


# ============================================================
# UTILIDADES
# ============================================================
def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):  # PyInstaller
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def save_csv(trends, output_path):
    now = datetime.now()
    df = pd.DataFrame({
        "fecha": [now.strftime("%Y-%m-%d")] * len(trends),
        "hora": [now.strftime("%H:%M:%S")] * len(trends),
        "tendencia": trends
    })

    if os.path.exists(output_path):
        df.to_csv(output_path, mode="a", header=False, index=False)
    else:
        df.to_csv(output_path, index=False)

    log.info(f"Tendencias guardadas en {output_path}")


# ============================================================
# RUNNER PRINCIPAL
# ============================================================
def run_scraper():
    log.info("Iniciando scraper...")

    chromedriver_path = resource_path(os.path.join("drivers", "chromedriver.exe"))
    cookies_path = resource_path("cookies.json")

    scraper = Scraper(chromedriver_path, cookies_path)

    try:
        trends = scraper.get_trending_topics()

        if not trends:
            log.warning("No se obtuvieron tendencias (posibles cookies inválidas).")
            return

        log.info("Tendencias obtenidas:")
        for i, t in enumerate(trends, 1):
            print(f"{i}. {t}")

        # Guardado temporal en CSV (antes de integrar DB)
        output_path = os.path.join(os.path.dirname(__file__), "tendencias.csv")
        save_csv(trends, output_path)

        log.info("Proceso completado con éxito.")

    finally:
        scraper.close()


if __name__ == "__main__":
    run_scraper()