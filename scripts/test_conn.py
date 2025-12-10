import sys
import os

# Agregar el path raíz del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db import _engine


def test_connection():
    try:
        with _engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Conexión exitosa:", result.scalar())
    except Exception as e:
        print("Error al conectar:", e)


if __name__ == "__main__":
    test_connection()
