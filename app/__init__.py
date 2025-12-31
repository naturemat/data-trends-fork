from flask import Flask
from flask_cors import CORS
from app.routes import routes_blueprint
import os

def create_app():
    # Detecta la ruta real de la carpeta donde está este archivo (__init__.py)
    # y sube un nivel para encontrar /frontend
    base_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_path = os.path.abspath(os.path.join(base_dir, "..", "frontend"))

    app = Flask(
        __name__,
        template_folder=frontend_path,
        static_folder=frontend_path,
        static_url_path=""
    )
    CORS(app)  # Habilita CORS para todas las rutas
    app.register_blueprint(routes_blueprint)
    return app
