import os
import pytest
from pymongo import MongoClient
from dotenv import load_dotenv

# Carga las variables de tu archivo .env
load_dotenv()

def test_mongo_connection():
    """Prueba de conexión a MongoDB usando la URL del .env"""
    mongo_uri = os.getenv("MONGODB_URL")
    print(f"\nProbando conexión a: {mongo_uri}") # Para ver si la lee bien
    
    assert mongo_uri is not None, "Error: MONGODB_URL no está en el .env"

    try:
        # Intenta conectar (timeout de 5 segundos para que no se cuelgue)
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # El comando ping confirma que hay conexión real
        client.admin.command('ping')
        print("✅ ¡Conexión Exitosa!")
        assert True
    except Exception as e:
        pytest.fail(f"❌ Falló la conexión a MongoDB: {e}")