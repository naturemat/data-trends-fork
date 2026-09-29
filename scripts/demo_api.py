#!/usr/bin/env python3
"""
Demo script para probar la API de tendencias.
Ejecutar despues de iniciar el servidor Flask.

Los endpoints que se consultan son los reales del blueprint de app/routes.py.
Los que dependen de fechas se piden sin rango, que hace que el backend use el
dia de la ultima captura almacenada.
"""

import os

import requests

BASE_URL = "http://localhost:5000"


def get_and_show(path, label, keys=None):
    """Consulta un endpoint GET y muestra los campos indicados."""
    print("=== " + label + " ===")
    try:
        response = requests.get(BASE_URL + path, timeout=30)
    except requests.exceptions.RequestException as e:
        print("Error de conexion: " + str(e))
        print()
        return None

    if response.status_code != 200:
        print("Error " + str(response.status_code) + ": " + response.text)
        print()
        return None

    payload = response.json()
    if keys:
        for key in keys:
            print(key + ": " + str(payload.get(key)))
    else:
        data = payload.get("data", payload)
        if isinstance(data, list):
            print("Elementos recibidos: " + str(len(data)))
            for item in data[:3]:
                print("  " + str(item))
        else:
            print(data)
    print()
    return payload


def test_last_update():
    """Comprueba que la API responde y cuando fue el ultimo scrape."""
    return get_and_show("/api/last_update", "ULTIMA ACTUALIZACION", ["last_update"])


def test_summary():
    """Totales del dashboard."""
    return get_and_show("/api/metrics/summary?pais=worldwide", "RESUMEN", [
        "total_unique", "total_global", "total_paises",
    ])


def test_persistence():
    """Top de tendencias mas persistentes."""
    return get_and_show("/api/metrics/persistence?pais=worldwide", "PERSISTENCIA")


def test_activity():
    """Actividad por intervalo de tiempo."""
    return get_and_show("/api/metrics/activity?pais=worldwide&granularity=hour", "ACTIVIDAD")


def test_spread():
    """Alcance geografico de las tendencias."""
    return get_and_show("/api/metrics/spread?pais=worldwide", "ALCANCE")


def test_survival():
    """Distribucion por horas de supervivencia."""
    return get_and_show("/api/metrics/survival?pais=worldwide", "SUPERVIVENCIA")


def test_ai_summary():
    """Resumen en lenguaje natural generado con Groq.

    Consume la API de IA, se omite con SKIP_AI=1 para no gastar cuota.
    """
    print("=== RESUMEN CON IA ===")
    persistence = get_and_show("/api/metrics/persistence?pais=worldwide", "PERSISTENCIA")
    if not persistence:
        return

    trends = persistence.get("data", [])[:15]
    if not trends:
        print("No hay tendencias suficientes para generar el resumen")
        print()
        return

    try:
        response = requests.post(
            BASE_URL + "/api/ai_summary",
            json={"data": trends, "pais_nombre": "Worldwide"},
            timeout=120,
        )
    except requests.exceptions.RequestException as e:
        print("Error de conexion: " + str(e))
        print()
        return

    if response.status_code == 200:
        print(response.json().get("summary", ""))
    else:
        print("Error " + str(response.status_code) + ": " + response.text)
    print()


def main():
    """Ejecuta todas las pruebas."""
    print("DEMO DE LA API DE TENDENCIAS")
    print("Base: " + BASE_URL)
    print("=" * 50)

    test_last_update()
    test_summary()
    test_persistence()
    test_activity()
    test_spread()
    test_survival()

    if os.environ.get("SKIP_AI") != "1":
        test_ai_summary()
    else:
        print("Prueba de IA omitida (SKIP_AI=1)")

    print("=" * 50)
    print("DEMO COMPLETADA")


if __name__ == "__main__":
    main()
