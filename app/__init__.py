from flask import Flask
from flask_cors import CORS
from app.routes import routes_blueprint

def create_app():
    app = Flask(
        __name__,
        # Mantenemos la configuración del frontend de tu amigo
        template_folder="../frontend",
        static_folder="../frontend",
        static_url_path=""
    )
    
    CORS(app) # Habilita CORS
    
    # AQUI ESTA EL ARREGLO: Agregamos el prefijo /api
    # Esto separa la web visual (/) de los datos (/api)
    app.register_blueprint(routes_blueprint, url_prefix='/api')
    
    return app