"""Flask route handlers for trends API."""

from flask import Blueprint, request, jsonify
from app.crud import create_trend, get_trends, get_trends_by_country, get_trends_by_date_range, save_scraped_trends, Trend, get_latest_per_day
import os
import json
import requests
from openai import OpenAI

routes_blueprint = Blueprint("routes", __name__)

GROQCLOUD_API_KEY = os.environ.get("GROQCLOUD_API_KEY")

# Configuración del cliente OpenAI (Groq)
client = OpenAI(
    api_key=GROQCLOUD_API_KEY,
    base_url="https://api.groq.com/openai/v1"  # endpoint de Groq
)

@routes_blueprint.get("/trends")
def list_trends():
    """Obtiene tendencias."""
    limit = request.args.get("limit", default=None, type=int)  # None si no se pasa
    pais = request.args.get("pais")
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    daily = request.args.get("daily", "false").lower() == "true"  # <-- nuevo

    if daily:
        # Obtiene el último registro de cada día
        trends = get_latest_per_day(pais)
    elif fecha_inicio and fecha_fin:
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

@routes_blueprint.get("/last_update")
def last_update():
    """Devuelve la fecha y hora del último registro."""
    latest = Trend.collection.find().sort("scraped_at", -1).limit(1)
    latest = list(latest)
    if latest:
        scraped_at = latest[0]["scraped_at"]  # datetime
        return jsonify({
            "last_update": scraped_at.strftime("%d/%m/%Y %H:%M:%S")
        })
    return jsonify({"last_update": "No hay registros"})

@routes_blueprint.post("/ai_summary")
def ai_summary():
    content = request.json or {}
    data = content.get("data", [])

    if not data:
        return jsonify({"summary": "No hay datos para generar resumen"}), 400

    # 1️⃣ Normalizar y proteger datos (evita KeyError)
    cleaned_data = [
        {
            "trend": d.get("trend"),
            "country": d.get("country"),
            "tweet_count": d.get("tweet_count", 0)
        }
        for d in data
        if d.get("trend") and d.get("country")
    ]

    if not cleaned_data:
        return jsonify({"summary": "Datos insuficientes para análisis"}), 400

    # 2️⃣ Agrupar por tendencia para eliminar duplicados
    aggregated = {}
    for d in cleaned_data:
        key = d["trend"].lower().strip()
        aggregated.setdefault(key, {
            "trend": d["trend"],
            "countries": set(),
            "tweet_count": 0
        })
        aggregated[key]["countries"].add(d["country"])
        aggregated[key]["tweet_count"] += d["tweet_count"]

    # 3️⃣ Convertir a lista y ordenar por impacto
    aggregated_list = [
        {
            "trend": v["trend"],
            "country": ", ".join(list(v["countries"])[:3]),  # limitar países
            "tweet_count": v["tweet_count"]
        }
        for v in aggregated.values()
    ]

    top_data = sorted(
        aggregated_list,
        key=lambda x: x["tweet_count"],
        reverse=True
    )[:30]  # menos datos = mejor resumen + menos tokens

    # 4️⃣ Construir texto para la IA (igual que antes)
    trends_text = "\n".join(
        f"{d['trend']} ({d['country']}): {d['tweet_count']} tweets"
        for d in top_data
    )

    prompt = (
        "Genera un resumen conciso de las tendencias de Twitter usando SOLO texto plano. "
        "Debe ser corto. "
        "No uses tablas, Markdown, listas numeradas ni viñetas. "
        "Enfócate en los patrones principales y temas más relevantes. "
        "Describe únicamente los temas dominantes, patrones generales y posibles contextos relevantes. "
        f"Datos:\n{trends_text}\nResumen:"
    )

    try:
        chat_completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}]
        )

        summary = chat_completion.choices[0].message.content.strip()

    except Exception as e:
        print("Error con GroqCloud:", e)
        summary = "Error generando resumen con IA"

    return jsonify({"summary": summary})

