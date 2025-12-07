import os
import sys
import pandas as pd
from datetime import datetime
from modules.scraper import Scraper


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)


def save_csv(trends, output_path):
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    hour = now.strftime("%H:%M:%S")

    df_new = pd.DataFrame({
        "Fecha": [today] * len(trends),
        "Hora": [hour] * len(trends),
        "Tendencia": trends
    })

    # Si el archivo ya existe → agregar sin cabecera
    if os.path.exists(output_path):
        df_new.to_csv(output_path, mode="a", header=False, index=False)
    else:
        df_new.to_csv(output_path, index=False)

    print(f"✔ Tendencias guardadas en CSV: {output_path}")

def run_scraper():
    chromedriver_path = resource_path(os.path.join("drivers", "chromedriver.exe"))
    cookies_path = resource_path("cookies.json")

    print("Iniciando scraper...\n")

    scraper = Scraper(chromedriver_path=chromedriver_path, cookies_path=cookies_path)

    try:
        # Obtener tendencias
        trends = scraper.get_trending_topics()

        if not trends:
            print("No se obtuvieron tendencias (posible problema de cookies/login).")
            return

        print("\nTendencias obtenidas:")
        for i, t in enumerate(trends, start=1):
            print(f"{i}. {t}")

        # Guardar CSV (ruta local)
        output_path = os.path.join(os.path.dirname(__file__), "tendencias.csv")
        save_csv(trends, output_path)

        print("\n✔ Finalizado correctamente.\n")

    finally:
        scraper.close()


if __name__ == "__main__":
    run_scraper()