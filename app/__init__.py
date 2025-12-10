from flask import Flask
from app.routes import routes_blueprint

def create_app():
    app = Flask(__name__)
    app.register_blueprint(routes_blueprint)
    return app
