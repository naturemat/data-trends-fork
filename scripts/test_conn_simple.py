import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener URL de MongoDB
mongodb_url = os.getenv("MONGODB_URL")

if not mongodb_url:
    print("Error: MONGODB_URL no encontrada en .env")
    exit(1)

def test_connection():
    try:
        # Conectar a MongoDB
        client = MongoClient(mongodb_url)
        db = client.get_database()

        # Ping a la base de datos
        db.command("ping")
        print("✅ Conexión exitosa a MongoDB")

        # Mostrar información
        print(f"📊 Base de datos: {db.name}")
        collections = db.list_collection_names()
        print(f"📁 Colecciones: {collections}")

        # Cerrar conexión
        client.close()

    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    test_connection()