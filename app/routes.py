"""Flask route handlers for trends API."""

from flask import Blueprint, request, jsonify
from app.crud import create_trend, get_trends, get_trends_by_country, get_trends_by_date_range, save_scraped_trends

routes_blueprint = Blueprint("routes", __name__)


@routes_blueprint.get("/trends")
def list_trends():
    """Obtiene todas las tendencias."""
    limit = request.args.get("limit", 100, type=int)
    pais = request.args.get("pais")
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")

    if fecha_inicio and fecha_fin:
        trends = get_trends_by_date_range(fecha_inicio, fecha_fin, limit)
    elif pais:
        trends = get_trends_by_country(pais, limit)
    else:
        trends = get_trends(limit)

    return jsonify(trends)


@routes_blueprint.post("/trends")
def add_trend():
    """Crea una nueva tendencia manualmente."""
    data = request.json
    if not data or "tendencia" not in data:
        return jsonify({"error": "tendencia es requerido"}), 400

    trend_id = create_trend(
        tendencia=data["tendencia"],
        numeroDeTwits=data.get("numeroDeTwits"),
        pais=data.get("pais", "worldwide")
    )
    return jsonify({"message": "Trend creado", "id": trend_id}), 201


@routes_blueprint.post("/trends/bulk")
def add_trends_bulk():
    """Guarda múltiples tendencias del scraper."""
    data = request.json
    if not data or not isinstance(data, list):
        return jsonify({"error": "Se espera una lista de tendencias"}), 400

    count = save_scraped_trends(data)
    return jsonify({"message": f"{count} tendencias guardadas"}), 201


@routes_blueprint.get("/trends/countries")
def get_countries():
    """Obtiene la lista de países disponibles."""
    # Esto podría ser una colección separada o calculado dinámicamente
    countries = ["worldwide", "united-states", "spain", "mexico", "argentina"]  # Ejemplo
    return jsonify({"countries": countries})
