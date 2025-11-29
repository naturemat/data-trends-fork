Instagram Scraper – Benford Analysis

Este proyecto es un scraper en Python que utiliza Selenium para obtener la cantidad de seguidores de los seguidores (o seguidos) de un usuario objetivo de Instagram.
Luego aplica la Ley de Benford para estimar si dicha cuenta se comporta como un usuario real o un posible bot, basado en la distribución de los primeros dígitos.

Características

	Ingresa el usuario objetivo por consola.
	Extrae seguidores o seguidos mediante Selenium.
	Inicia sesión automáticamente usando cookies (si existen).
	Si no hay cookies válidas, permite ingresar usuario y contraseña.
	Obtiene seguidores de cada usuario listado.
	Limpia, valida y tabula los datos.
	Aplica Ley de Benford al dataset recolectado.

Genera:

	Tabla general
	Frecuencias de primeros dígitos
	Gráfica comparativa
	Conclusión automática (“real” o “bot”)

Estructura del proyecto
instagram-scraper/
│── modules/
│   ├── scraper.py
│   ├── utils.py
│── drivers/
│── main.py
│── README.md
│── requirements.txt
│── .gitignore

Requisitos

	Python 3.8+
	Google Chrome instalado
	ChromeDriver compatible

Instalación

	Clona el repositorio:

		git clone https://github.com/tu-usuario/instagram-scraper.git
		cd instagram-scraper


Instala dependencias:

	pip install -r requirements.txt


Coloca tu chromedriver.exe dentro de la carpeta drivers/.

Crea un archivo cookies.json con tu sesión iniciada.

Cómo ejecutar

	Desde la raíz del proyecto:
	python main.py


El programa pedirá:

	El usuario objetivo
	Si quieres analizar followers o following
	Cargará cookies o pedirá login
	Mostrará tabla
	Mostrará gráfica
	Entregará conclusión

Advertencia importante sobre Instagram

	Instagram puede bloquear:
	Acceso automatizado
	Scraping excesivo
	Inicios de sesión sospechosos
	Uso de cookies de terceros

Este proyecto es solo con fines educativos y de análisis.
Úsalo únicamente en cuentas con permiso explícito.