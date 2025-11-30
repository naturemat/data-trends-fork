import math
import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter

from modules.scraper import Scraper

def plot_word_frequencies(words_counts):
    palabras, cuentas = zip(*words_counts)
    plt.figure(figsize=(12,6))
    plt.bar(palabras, cuentas, color='skyblue')
    plt.title("Palabras más frecuentes en tendencias de X")
    plt.xlabel("Palabras")
    plt.ylabel("Frecuencia")
    plt.xticks(rotation=45)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()

def main():
    chromedriver_path = r"D:\Usuario\Documentos\U\SEMESTRE_6\Desarrollo\x-scraper\drivers\chromedriver.exe"  # Cambia la ruta a tu chromedriver
    cookies_path = r"D:\Usuario\Documentos\U\SEMESTRE_6\Desarrollo\x-scraper\cookies.json" # Cambia la ruta a tu archivo de cookies

    scraper = Scraper(chromedriver_path=chromedriver_path, cookies_path=cookies_path)

    # Obtener tendencias
    trends = scraper.get_trending_topics()
    if not trends:
        print("No se obtuvieron tendencias. Revisa cookies o login.")
        scraper.close()
        return

    print("\nTendencias obtenidas:")
    for i, t in enumerate(trends, 1):
        print(f"{i}. {t}")

    # Contar palabras
    word_counts = scraper.count_words_in_trends(trends)
    print("\nPalabras más frecuentes:")
    for w, c in word_counts:
        print(f"{w}: {c}")

    # Crear dataframe y guardar CSV
    df = pd.DataFrame(word_counts, columns=["Palabra", "Frecuencia"])
    df.to_csv("palabras_tendencias.csv", index=False)
    print("\nArchivo 'palabras_tendencias.csv' guardado.")

    # Graficar
    plot_word_frequencies(word_counts)

    scraper.close()

if __name__ == "__main__":
    main()