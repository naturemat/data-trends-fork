import os

import pytest
from dotenv import load_dotenv
from pymongo import MongoClient

# Carga las variables del archivo .env
load_dotenv()


def mask_credentials(uri):
    """Oculta usuario y contrasena de una URI de Mongo.

    La URI lleva la contrasena dentro, asi que registrarla tal cual la
    escribiria en el log de CI.
    """
    if "//" not in uri or "@" not in uri:
        return uri

    esquema, resto = uri.split("//", 1)
    credenciales, host = resto.rsplit("@", 1)
    usuario = credenciales.split(":")[0]

    return esquema + "//" + usuario + ":***@" + host


def test_mongo_connection():
    """Comprueba que MONGODB_URL este definido y que el servidor responda."""
    mongo_uri = os.getenv("MONGODB_URL")
    assert mongo_uri is not None, "MONGODB_URL no esta definido en el .env"

    print("\nProbando conexion a: " + mask_credentials(mongo_uri))

    client = None
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # El comando ping confirma que hay conexion real
        client.admin.command("ping")
        print("Conexion exitosa")
    except Exception as e:
        pytest.fail("Fallo la conexion a MongoDB: " + str(e))
    finally:
        if client is not None:
            client.close()
