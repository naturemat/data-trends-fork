from flask import Flask
from flask_cors import CORS
from app.routes import routes_blueprint

def create_app():
    app = Flask(
        __name__,
        # Mantenemos lo de tu amigo tal cual
        template_folder="../frontend",
        static_folder="../frontend",
        static_url_path=""
    )
    CORS(app) 
    
    # --- CAMBIO IMPORTANTE AQUÍ ---
    # Agrega url_prefix='/api' dentro del paréntesis
    app.register_blueprint(routes_blueprint, url_prefix='/api')
    
    return app