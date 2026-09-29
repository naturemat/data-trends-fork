import os

import scrapy

COUNTRIES_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, "countries.txt"
)


class scraper(scrapy.Spider):
    name = "trends"
    allowed_domains = ["trends24.in"]

    collected = None
    # Paises cuyo HTML no traia el contenedor esperado. Sirve para distinguir
    # "no hay tendencias" de "trends24.in cambio el marcado".
    empty_countries = None

    def start_requests(self):
        # Leer lista de países desde archivo (simple de editar en servidor)
        with open(COUNTRIES_FILE, "r", encoding="utf-8") as file:
            countries = file.read().splitlines()

        for country in countries:

            # Caso especial: worldwide no tiene ruta
            if country.lower() == "worldwide":
                url = "https://trends24.in"
            else:
                url = f"https://trends24.in/{country}/"

            yield scrapy.Request(
                url=url,
                callback=self.parse,
                cb_kwargs={"country": country}  # pasar el país real
            )

    def parse(self, response, country):

        first_block = response.css("div.list-container").get()

        if not first_block:
            if scraper.empty_countries is not None:
                scraper.empty_countries.append(country)
            return

        block = response.css("div.list-container")[0]
        items = block.css("li")
        
        clean_rows = []
        seen = set()

        for li in items:

            trend = li.css("a.trend-link::text").get()

            if not trend:
                continue

            trend = trend.strip()

            # Evitar duplicados
            if trend.lower() in seen:
                continue
            seen.add(trend.lower())

            row = { "trend": trend, "country": country, } 
            
            clean_rows.append(row) 
            yield row 
            
        # Modo Instagram-like: ademas de yield, se acumulan las filas en la
        # clase para que main.py pueda guardarlas todas juntas al terminar.
        if scraper.collected is not None: 
            scraper.collected.extend(clean_rows)