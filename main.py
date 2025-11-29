from modules.scraper import Scraper
from modules.utils import ask_input, ask_multiple_option
import matplotlib.pyplot as plt
import math
import pandas as pd
import os

def benford_analysis(data):
    print("\n=== ANÁLISIS LEY DE BENFORD ===")

    first_digits = []
    for user, followers in data.items():
        if isinstance(followers, int) and followers > 0:
            first_digits.append(int(str(followers)[0]))

    if not first_digits:
        print("No hay datos válidos para analizar.")
        return

    total = len(first_digits)
    freqs = {d: first_digits.count(d) / total * 100 for d in range(1, 10)}
    benford = {d: math.log10(1 + 1/d) * 100 for d in range(1, 10)}

    print(f"{'Dígito':<8}{'Observado (%)':<15}{'Benford (%)':<12}{'Desviación (%)':<15}")
    desviaciones = []
    for d in range(1, 10):
        desviacion = abs(freqs[d] - benford[d])
        desviaciones.append(desviacion)
        print(f"{d:<8}{freqs[d]:<15.2f}{benford[d]:<12.2f}{desviacion:<15.2f}")

    plt.figure(figsize=(9,5))
    plt.bar(freqs.keys(), freqs.values(), label="Frecuencia observada", alpha=0.7, color='skyblue')

    plt.plot(list(freqs.keys()), list(freqs.values()), 'b-o', linewidth=2, label="Tendencia observada")

    plt.plot(list(benford.keys()), list(benford.values()), 'r--o', linewidth=2, label="Ley de Benford (Real)")

    plt.xlabel("Primer dígito")
    plt.ylabel("Frecuencia (%)")
    plt.title("Comparación con la Ley de Benford")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()

    desviacion_promedio = sum(desviaciones) / 9
    print(f"\nDesviación promedio: {desviacion_promedio:.2f}%")

    if desviacion_promedio <= 12:
        print("Conclusión: Cuenta real (desviacion inferior al 12%).")
    else:
        print("Conclusión: Cuenta bot (desviación superior al 12%).")

groups = ['followers', 'following']

target = ask_input('Enter the target username: ')
group = ask_multiple_option(options = groups)


from modules.scraper import Scraper

def scrape(group):
    chromedriver_path = os.path.join("drivers", "chromedriver.exe")
    cookies_path = "cookies.json"

    driver = Scraper.create_driver(chromedriver_path)
    
    print("Intentando cargar cookies desde cookies.json...")
    session_ok = Scraper.load_simple_cookies_and_auth(driver, cookies_path)

    scraper = Scraper(target)
    scraper.driver = driver

    if not session_ok:
        username = ask_input('Username: ')
        password = ask_input(is_password = True)
        scraper.authenticate(username, password)

    links = scraper.get_users(group, verbose=True)
    print(f"Se obtuvieron {len(links)} usuarios.")
    
    followers_count = scraper.get_followers_count(links)

    print("\nResultados:")

    scraper.close()

    if followers_count:
        tabla = pd.DataFrame(list(followers_count.items()), columns=["Usuario", "Número de Seguidores"])
    
        tabla = tabla[tabla["Número de Seguidores"].apply(lambda x: str(x).isdigit() and int(x) > 0)]
    
        tabla["Número de Seguidores"] = tabla["Número de Seguidores"].astype(int)
    
        tabla["Primer Dígito"] = tabla["Número de Seguidores"].apply(lambda x: int(str(x)[0]))

        print("\n=== TABLA DE RESULTADOS ===")
        print(tabla.to_string(index=False))
    
        freq_tabla = (
        tabla["Primer Dígito"]
        .value_counts()
        .sort_index()
        .reindex(range(1, 10), fill_value=0)
        .reset_index()
        )
        freq_tabla.columns = ["Dígito", "Frecuencia"]

        print("\n=== FRECUENCIA DE PRIMEROS DÍGITOS ===")
        print(freq_tabla.to_string(index=False))

        benford_analysis(dict(zip(tabla["Usuario"], tabla["Número de Seguidores"])))

    else:
        print("\nNo se obtuvieron seguidores para mostrar en la tabla.")

if __name__ == "__main__":
        scrape(group)