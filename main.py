import os
import logging
import sys
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv 

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from modules.scraper import scraper
from app.crud import save_scraped_trends 
from app.models import ensure_indexes

# El CSV se rota al llegar a este tamano para que no crezca sin limite.
CSV_MAX_BYTES = 20 * 1024 * 1024

# ============================================================
# CONFIG LOGGING
# ============================================================
logging.disable(logging.DEBUG)
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("Runner")

# ============================================================
# CARGA DE VARIABLES DE ENTORNO (.env)
# ============================================================
# Se resuelve relative al archivo, no a una ruta fija de un servidor,
# para que funcione igual en local y en el despliegue.
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

if not load_dotenv(env_path):
    log.warning(f"No se encontro un archivo .env en {env_path}, se usara el entorno actual")
else:
    log.info(f".env cargado correctamente desde {env_path}")


# ============================================================
# UTILIDADES
# ============================================================
def rotate_csv_if_needed(output_path):
    """Rota el CSV cuando supera CSV_MAX_BYTES, conservando una copia."""
    if not os.path.exists(output_path):
        return
    if os.path.getsize(output_path) < CSV_MAX_BYTES:
        return

    backup = output_path + ".1"
    if os.path.exists(backup):
        os.remove(backup)
    os.replace(output_path, backup)
    log.warning(
        f"{output_path} supero {CSV_MAX_BYTES} bytes, se rotó a {backup}"
    )


def save_csv(trends, output_path):
    now = datetime.now().strftime("%Y-%m-%d")
    hour = datetime.now().strftime("%H:%M:%S")

    df = pd.DataFrame(trends)

    df.insert(0, "fecha", now)
    df.insert(1, "hora", hour)

    rotate_csv_if_needed(output_path)

    if os.path.exists(output_path):
        df.to_csv(output_path, mode="a", header=False, index=False)
    else:
        df.to_csv(output_path, index=False)

    log.info(f"Tendencias guardadas en {output_path}")


# ============================================================
# INTEGRACIÓN CON MONGODB
# ============================================================
def save_to_database(trends):
    """Guarda las tendencias en MongoDB."""
    try:
        count = save_scraped_trends(trends)
        log.info(f"{count} tendencias guardadas en MongoDB")
        return count
    except Exception as e:
        log.error(f"Error guardando en MongoDB: {e}")
        return 0


# ============================================================
# RUNNER PRINCIPAL
# ============================================================
def run_scraper(save_to_db=True):
    log.info("Iniciando scraper...")

    collected = []

    scraper.collected = collected
    scraper.empty_countries = []

    settings = get_project_settings()
    scraper_logger = logging.getLogger("scrapy.core.scraper")
    scraper_logger.handlers.clear()
    scraper_logger.propagate = False
    scraper_logger.disabled = True
    
    logging.getLogger("scrapy.utils.log").disabled = True
    
    process = CrawlerProcess(settings={
            "LOG_ENABLED": False,          # apaga TODO Scrapy
            "TELNETCONSOLE_ENABLED": False,
            "LOG_LEVEL": "WARNING",
            "LOG_SCRAPED_ITEMS": False,
            "STATS_DUMP": False,
            "LOGSTATS_INTERVAL": 0,
        })

    process.crawl(scraper)

    try:
        process.start()
    except Exception:
        log.exception("El crawler fallo antes de terminar, no se guarda nada")
        return 1

    trends = collected

    if scraper.empty_countries:
        log.warning(
            "Paises sin datos: %s. Si son todos, lo mas probable es que "
            "trends24.in haya cambiado sus clases y el selector "
            "'div.list-container' ya no coincida.",
            ", ".join(scraper.empty_countries)
        )

    # Antes esto solo escribia un warning y salia con codigo 0, de modo que
    # cron daba el scrape por bueno mientras el dashboard servia datos viejos.
    if not trends:
        log.error(
            "No se obtuvieron tendencias en ninguna consulta. No se guardo nada."
        )
        return 1

    if save_to_db:
        db_count = save_to_database(trends)
        if db_count > 0:
            log.info("Datos guardados exitosamente en la base de datos")
        else:
            log.error("No se pudo guardar nada en MongoDB")
            return 1

    output_path = os.path.join(os.path.dirname(__file__), "tendencias.csv")
    save_csv(trends, output_path)

    log.info("Proceso completado con éxito.")
    return 0

if __name__ == "__main__":
    ensure_indexes()
    sys.exit(run_scraper())