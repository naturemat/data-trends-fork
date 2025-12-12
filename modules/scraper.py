import scrapy

class scraper(scrapy.Spider):
    name = "trends"
    allowed_domains = ["trends24.in"]

    collected = None

    def start_requests(self):
        # Leer lista de países desde archivo (simple de editar en servidor)
        with open("countries.txt", "r") as file:
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

        items = response.css("li.bg-sky-50, li.dark\\:bg-slate-950, li")

        clean_rows = []
        seen = set()

        for li in items:

            trend = li.css("a.trend-link::text").get()
            count_raw = li.css(".tweet-count::attr(data-count)").get()

            if not trend:
                continue

            trend = trend.strip()

            # Evitar duplicados
            if trend.lower() in seen:
                continue
            seen.add(trend.lower())

            tweet_count = int(count_raw) if count_raw and count_raw.isdigit() else None

            row = {
                "trend": trend,
                "tweet_count": tweet_count,
                "country": country,  # viene desde start_requests
            }

            clean_rows.append(row)
            yield row

        # para modo tipo Instagram-like
        if scraper.collected is not None:
            scraper.collected.extend(clean_rows)