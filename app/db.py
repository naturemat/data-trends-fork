import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# --- CARGA SEGURA DEL .ENV ---
# Buscamos el .env subiendo un nivel desde la carpeta 'app/'
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

MONGODB_URL = os.getenv("MONGODB_URL")

# Debug: Esto saldrá en tus logs para confirmar la conexión
if not MONGODB_URL:
    print("CRITICAL: MONGODB_URL no cargó desde .env, usando fallback...")
    # Puedes poner tu URL real aquí como último recurso (fallback)
    MONGODB_URL = "mongodb://Grupo1:passGrupo1@3.151.181.99:27017/scraper_db?authSource=admin"

# Cliente MongoDB
client = MongoClient(MONGODB_URL)

# Base de datos (especificamos el nombre por seguridad)
db = client.scraper_db

def get_database():
    return db

def close_connection():
    client.close()