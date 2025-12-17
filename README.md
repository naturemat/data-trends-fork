# X Trends Scraper con Backend MongoDB

Este proyecto es un scraper en Python que utiliza Scrapy para obtener las tendencias (topics, hashtags, o temas populares) actuales en X (antes Twitter), y las almacena en MongoDB para servirlas a través de una API REST con Flask.

## Características

* ✅ Extrae las tendencias actuales de X automáticamente con Scrapy
* ✅ Limpia, valida y estructura los datos obtenidos
* ✅ Almacena datos en MongoDB para persistencia
* ✅ API REST con Flask para consultar tendencias
* ✅ Genera reportes CSV adicionales
* ✅ Arquitectura modular y escalable

## Estructura del proyecto

```
x-trends-scraper/
├── modules/           # Código del scraper (NO MODIFICAR)
│   └── scraper.py
├── app/              # Backend Flask + MongoDB
│   ├── __init__.py   # Configuración Flask
│   ├── db.py         # Conexión MongoDB
│   ├── models.py     # Modelos de documentos
│   ├── routes.py     # Endpoints API
│   └── crud.py       # Operaciones CRUD
├── scripts/          # Utilidades
│   ├── run.py        # Ejecutar servidor Flask
│   ├── test_conn.py  # Probar conexión MongoDB
│   └── demo_api.py   # Demo de la API
├── frontend/         # Interfaz web del dashboard
│   ├── index.html    # Página principal
│   ├── assets/       # Recursos estáticos como imágenes
│   ├── css/          # Hojas de estilo
│   └── js/           # Scripts de frontend
├── drivers/          # Drivers para scraping
├── main.py           # Ejecutar scraper
├── requirements.txt  # Dependencias
├── .env             # Variables de entorno
└── README.md
```

## Requisitos

* Python 3.12+
* MongoDB (local o remoto)
* Google Chrome instalado (para Scrapy/Selenium si se usa)

## Instalación

1. **Clona el repositorio:**
   ```bash
   git clone https://github.com/tu-usuario/x-trends-scraper.git
   cd x-trends-scraper
   ```

2. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configura MongoDB:**
   - Instala MongoDB localmente o usa un servicio en la nube
   - Actualiza `.env` con tu URL de MongoDB:
     ```
     MONGODB_URL=mongodb://localhost:27017/scraper_db
     ```

4. **Configura el scraper:**
   - Asegúrate de que `countries.txt` existe con la lista de países

5. **Configura el API Key de Groq**
   - Actualiza `.env` con tu API Key de Groq
     ```
     GROQCLOUD_API_KEY=API_KEY
     ```

## Cómo usar

### 1. Ejecutar el scraper (guarda en MongoDB + CSV)
```bash
python main.py
```

### 2. Iniciar el servidor API
```bash
python scripts/run.py
```

### 3. Probar la API
```bash
python scripts/demo_api.py
```

### 4. Ver tendencias desde el navegador
- GET `/trends` - Todas las tendencias
- GET `/trends?country=spain&limit=10` - Tendencias por país
- POST `/trends` - Crear tendencia manual
- POST `/trends/bulk` - Insertar múltiples tendencias

## API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/trends` | Obtener tendencias (parámetros: `limit`, `country`) |
| POST | `/trends` | Crear tendencia manual |
| POST | `/trends/bulk` | Insertar tendencias del scraper |
| GET | `/trends/countries` | Lista de países disponibles |

## Variables de entorno

```env
MONGODB_URL=mongodb://localhost:27017/scraper_db
FLASK_ENV=development
SECRET_KEY=tu_clave_secreta_aqui
```

## Desarrollo

### Ejecutar tests
```bash
python -m pytest tests/
```

### Probar conexión a BD
```bash
python scripts/test_conn.py
```

### Ver logs detallados
```bash
python main.py  # Logs del scraper
python scripts/run.py  # Logs del servidor Flask
```

## Advertencias importantes

* ⚠️ X puede bloquear o limitar accesos automatizados
* ⚠️ Evita hacer scraping excesivo para no ser bloqueado
* ⚠️ Respeta los términos de servicio de X
* ⚠️ Usa delays apropiados entre requests

## Tecnologías

- **Scrapy**: Web scraping framework
- **Flask**: Web framework para la API
- **MongoDB**: Base de datos NoSQL
- **PyMongo**: Driver MongoDB para Python
- **Pandas**: Procesamiento de datos
* Respeta los términos de servicio de X y usa este proyecto solo con fines educativos o análisis autorizado.