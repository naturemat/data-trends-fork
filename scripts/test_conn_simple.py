import os

from dotenv import load_dotenv
from pymongo import MongoClient

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
        print("Conexion exitosa a MongoDB")

        # Mostrar informacion
        print("Base de datos: " + db.name)
        collections = db.list_collection_names()
        print("Colecciones: " + str(collections))

        # Cerrar conexion
        client.close()

    except Exception as e:
        print("Error de conexion: " + str(e))


if __name__ == "__main__":
    test_connection()
