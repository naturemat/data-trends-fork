import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# --- CARGA SEGURA DEL .ENV ---
# Buscamos el .env subiendo un nivel desde la carpeta 'app/'
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

MONGODB_URL = os.getenv("MONGODB_URL")

if not MONGODB_URL:
    raise RuntimeError(
        "MONGODB_URL no esta definido. Configuralo en el archivo .env "
        "(ver .env.example) o exportalo en el entorno antes de arrancar."
    )

# Cliente MongoDB
client = MongoClient(MONGODB_URL)

# Base de datos (especificamos el nombre por seguridad)
db = client.scraper_db

def get_database():
    return db

def close_connection():
    client.close()