import pytest
import sys
import os

# --- Configuración de rutas ---
# Esto permite importar modulos desde la carpeta superior 'scraper'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- IMPORTACIÓN CORRECTA ---
# Importamos la función 'create_app' desde la carpeta 'app'
try:
    from app import create_app
except ImportError as e:
    raise ImportError(f"No se pudo importar 'create_app' desde el paquete 'app'. Error: {e}")

@pytest.fixture
def client():
    """
    Configura un cliente de prueba de Flask.
    Como usas 'create_app', debemos llamar a esa función primero.
    """
    # 1. Fabricamos la app
    app = create_app()
    
    # 2. Configuramos modo testing (importante para ver errores detallados)
    app.config['TESTING'] = True
    
    # 3. Entregamos el cliente para las pruebas
    with app.test_client() as client:
        yield client

def test_routes_exist(client):
    """
    Verifica que la API responda en la nueva ruta con prefijo.
    """
    # Cambiamos '/trends' por '/api/trends'
    response = client.get('/api/trends')
    
    # Verificamos que NO sea 404 (o sea, que la ruta exista)
    assert response.status_code != 404, "La API no responde en /api/trends"
def test_trends_endpoint_structure(client):
    """
    Prueba de datos: Verificar que recibimos un JSON válido.
    """
    response = client.get('/trends')
    
    if response.status_code == 200:
        assert response.is_json, "El endpoint debería devolver JSON"
        data = response.get_json()
        assert isinstance(data, list), "Se esperaba una lista de tendencias"
        
        # Opcional: Verificar que no esté vacío (solo pasará si ya escrapeaste datos)
        # assert len(data) > 0, "La lista de tendencias está vacía"