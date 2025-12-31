from flask import Flask, jsonify  # <--- AGREGAMOS jsonify AQUÍ
from flask_cors import CORS
from app.routes import routes_blueprint

def create_app():
    app = Flask(
        __name__,
        template_folder="../frontend",
        static_folder="../frontend",
        static_url_path=""
    )
    CORS(app)
    
    # Registramos tus rutas normales bajo /api
    app.register_blueprint(routes_blueprint, url_prefix='/api')

    # --- AGREGAMOS ESTO PARA QUE FUNCIONE EL FRONTEND ---
    # Esta ruta va "suelta" (sin /api) para que el JS la encuentre en /config
    @app.route('/config')
    def config():
        return jsonify({"api_base": "/api"}) 
        # OJO: Aquí le decimos al JS que las demas rutas (trends, etc) estan en /api

    return app