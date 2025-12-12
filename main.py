import os
import sys
import logging
from datetime import datetime
import pandas as pd

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from modules.scraper import scraper


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
    now = datetime.now().strftime("%Y-%m-%d")
    hour = datetime.now().strftime("%H:%M:%S")

    # Convertimos a DataFrame correctamente
    df = pd.DataFrame(trends)

    # Añadimos las columnas de fecha y hora
    df.insert(0, "fecha", now)
    df.insert(1, "hora", hour)

    # Guardamos como columnas verdaderas
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

    # Contenedor donde se guardarán los resultados del spider
    collected = []

    # El spider recibirá este contenedor para llenar tendencias
    scraper.collected = collected

    settings = get_project_settings()
    process = CrawlerProcess(settings)

    process.crawl(scraper)
    process.start()  # Bloquea hasta que el spider termina

    trends = collected

    if not trends:
        log.warning("No se obtuvieron tendencias.")
        return

    log.info("Tendencias obtenidas:")
    for i, t in enumerate(trends, 1):
        print(f"{i}. {t}")

    output_path = os.path.join(os.path.dirname(__file__), "tendencias.csv")
    save_csv(trends, output_path)

    log.info("Proceso completado con éxito.")


if __name__ == "__main__":
    run_scraper()
