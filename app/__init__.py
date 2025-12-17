from flask import Flask
from flask_cors import CORS
from app.routes import routes_blueprint

def create_app():
    app = Flask(__name__)
    CORS(app)  # Habilita CORS para todas las rutas
    app.register_blueprint(routes_blueprint)
    return app
