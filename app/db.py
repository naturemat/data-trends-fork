import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
if not MONGODB_URL:
    raise RuntimeError("MONGODB_URL no está definido en el archivo .env")

# Cliente MongoDB (singleton)
client = MongoClient(MONGODB_URL)

# Base de datos
db: Database = client.get_database()

# Alias para compatibilidad
_database = db


def get_database():
    """Retorna la base de datos MongoDB."""
    return db


def close_connection():
    """Cierra la conexión a MongoDB."""
    client.close()
