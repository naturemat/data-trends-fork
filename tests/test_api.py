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
    Prueba básica: Verificar que la app arranca y no da 404 en todo.
    Intentamos acceder a una ruta que sepamos que existe.
    """
    # Si tienes una ruta raíz '/', úsala. Si no, usa '/trends' o '/api/trends'
    # Aquí probaremos '/trends' asumiendo que es tu ruta principal de datos
    response = client.get('/trends')
    
    # NOTA: Si tu ruta real es '/api/trends', cambia la línea de arriba.
    
    # Si devuelve 404, el test fallará y sabremos que la ruta está mal escrita
    assert response.status_code != 404, "La ruta '/trends' no fue encontrada (Error 404)"

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