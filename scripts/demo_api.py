#!/usr/bin/env python3
"""
Demo script para probar la API de tendencias.
Ejecutar después de iniciar el servidor Flask.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"


def test_get_trends():
    """Prueba obtener tendencias."""
    print("=== OBTENIENDO TENDENCIAS ===")
    response = requests.get(f"{BASE_URL}/trends?limit=5")
    if response.status_code == 200:
        trends = response.json()
        print(f"✓ {len(trends)} tendencias obtenidas")
        for i, trend in enumerate(trends[:3], 1):
            print(f"  {i}. {trend.get('hashtag', 'N/A')} - {trend.get('country', 'N/A')}")
    else:
        print(f"✗ Error: {response.status_code}")
    print()


def test_create_trend():
    """Prueba crear una tendencia."""
    print("=== CREANDO TENDENCIA MANUAL ===")
    data = {
        "tendencia": "#TestTrend",
        "numeroDeTwits": 1000,
        "pais": "test"
    }
    response = requests.post(f"{BASE_URL}/trends", json=data)
    if response.status_code == 201:
        result = response.json()
        print(f"✓ Tendencia creada: {result}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
    print()


def test_bulk_insert():
    """Prueba insertar múltiples tendencias (como del scraper)."""
    print("=== INSERTANDO TENDENCIAS A GRANEL ===")
    trends_data = [
        {"trend": "#Python", "tweet_count": 5000, "country": "worldwide"},
        {"trend": "#MongoDB", "tweet_count": 3000, "country": "worldwide"},
        {"trend": "#Flask", "tweet_count": 2000, "country": "worldwide"}
    ]
    response = requests.post(f"{BASE_URL}/trends/bulk", json=trends_data)
    if response.status_code == 201:
        result = response.json()
        print(f"✓ {result.get('message', 'Datos guardados')}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
    print()


def test_get_countries():
    """Prueba obtener países disponibles."""
    print("=== OBTENIENDO PAÍSES ===")
    response = requests.get(f"{BASE_URL}/trends/countries")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Países disponibles: {data.get('countries', [])}")
    else:
        print(f"✗ Error: {response.status_code}")
    print()


def main():
    """Ejecuta todas las pruebas."""
    print("🚀 DEMO DE LA API DE TENDENCIAS")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        test_get_trends()
        test_create_trend()
        test_bulk_insert()
        test_get_countries()

        print("✅ DEMO COMPLETADA")
        print("\n💡 Para usar desde el scraper:")
        print("   python main.py  # Guarda automáticamente en MongoDB + CSV")

    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se puede conectar al servidor Flask")
        print("   Asegúrate de ejecutar: python scripts/run.py")
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {e}")


if __name__ == "__main__":
    main()