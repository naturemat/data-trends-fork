# X Trends Scraper

Este proyecto es un scraper en Python que utiliza Selenium para obtener las tendencias (topics, hashtags, o temas populares) actuales en X (antes Twitter). 

## Características

* Extrae las tendencias actuales de X automáticamente con Selenium.
* Limpia, valida y estructura los datos obtenidos.
* Genera reportes con las tendencias recolectadas para análisis.

## Estructura del proyecto
x-trends-scraper/
│── modules/
│   ├── scraper.py
│   ├── utils.py
│── drivers/
│── main.py
│── README.md
│── requirements.txt
│── .gitignore

## Requisitos

* Python 3.8+
* Google Chrome instalado
* ChromeDriver compatible con tu versión de Chrome

## Instalación

Clona el repositorio:

git clone https://github.com/tu-usuario/x-trends-scraper.git
cd x-trends-scraper

Instala las dependencias:

pip install -r requirements.txt

Coloca tu `chromedriver.exe` dentro de la carpeta `drivers/`.

## Cómo ejecutar

Desde la raíz del proyecto ejecuta:

python main.py

## Advertencias importantes sobre scraping en X

* X puede bloquear o limitar accesos automatizados.
* Evita hacer scraping excesivo para no ser bloqueado.
* Respeta los términos de servicio de X y usa este proyecto solo con fines educativos o análisis autorizado.