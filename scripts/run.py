"""Arranque en local para desarrollo.

NO usar en produccion: el servidor de desarrollo de Flask no es para eso.
Para produccion ver deploy/scraper.service, que lanza gunicorn con
gunicorn.conf.py.
"""

from app import create_app
from app.models import ensure_indexes

app = create_app()

if __name__ == "__main__":
    # Los indices se crean al arrancar para que el entorno local no dependa
    # de que el script de inicializacion de Mongo se haya ejecutado.
    ensure_indexes()

    # debug=False a proposito. Con debug=True se activa el depurador de
    # Werkzeug, que permite ejecutar codigo remoto en el servidor.
    app.run(debug=False, host="127.0.0.1", port=5000)
