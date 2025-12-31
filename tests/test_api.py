import pytest
import sys
import os

# --- Configuración de rutas ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app import create_app
except ImportError as e:
    raise ImportError(f"No se pudo importar 'create_app' desde el paquete 'app'. Error: {e}")

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    """
    Verifica que la página principal (Frontend) cargue correctamente.
    """
    response = client.get('/')
    assert response.status_code == 200, "La ruta raíz '/' no funciona"

def test_config_route(client):
    """
    Verifica que el endpoint de configuración para el frontend exista.
    """
    response = client.get('/config')
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert "api_base" in data, "El JSON de configuración debe incluir 'api_base'"

def test_metrics_activity_exists(client):
    """
    Verifica que el endpoint de métricas de actividad responda (aunque sea con error de parámetros).
    """
    response = client.get('/api/metrics/activity')
    
    # Verificamos que NO sea 404. 
    # Puede devolver 200 (éxito) o 400 (si faltan parámetros), 
    # pero lo importante es que la ruta EXISTE.
    assert response.status_code != 404, "El endpoint /api/metrics/activity no fue encontrado"

def test_last_update_endpoint(client):
    """
    Verifica el endpoint de metadata.
    """
    response = client.get('/last_update')
    assert response.status_code == 200
    assert response.is_json