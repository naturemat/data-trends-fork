"""Flask route handlers for trends API."""

import os
from flask import Blueprint, request, jsonify, render_template
from openai import OpenAI

# CRUD y modelos
from app.crud import (
    get_trends,
    get_trends_by_country,
    get_trends_by_date_range,
    get_latest_per_day,
    Trend,
)

# ---------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------
routes_blueprint = Blueprint("routes", __name__)

# ---------------------------------------------------------------------
# Configuración IA (Groq / OpenAI compatible)
# ---------------------------------------------------------------------
GROQCLOUD_API_KEY = os.environ.get("GROQCLOUD_API_KEY")

client = OpenAI(
    api_key=GROQCLOUD_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

# ---------------------------------------------------------------------
# Obtener la instancia de Flask
# ---------------------------------------------------------------------
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000")

@routes_blueprint.get("/config")
def get_config():
    """Devuelve configuración pública para el frontend."""
    return jsonify({
        "api_base": API_BASE_URL
    })

# ---------------------------------------------------------------------
# Rutas de tendencias
# ---------------------------------------------------------------------

@routes_blueprint.get("/")
def index():
    return render_template("index.html")

@routes_blueprint.get("/trends")
def list_trends():
    """Obtiene tendencias con distintos filtros opcionales."""

    limit = request.args.get("limit", type=int)
    pais = request.args.get("pais")
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    daily = request.args.get("daily", "false").lower() == "true"

    if daily:
        trends = get_latest_per_day(pais)
    elif fecha_inicio and fecha_fin:
        trends = get_trends_by_date_range(fecha_inicio, fecha_fin, limit)
    elif pais:
        trends = get_trends_by_country(pais, limit)
    else:
        trends = get_trends(limit)

    return jsonify(trends)

@routes_blueprint.get("/last_update")
def last_update():
    """Devuelve la fecha y hora del último scraping."""

    latest = list(
        Trend.collection.find().sort("scraped_at", -1).limit(1)
    )

    if not latest:
        return jsonify({"last_update": "No hay registros"})

    scraped_at = latest[0]["scraped_at"]

    return jsonify({
        "last_update": scraped_at.strftime("%d/%m/%Y %H:%M:%S")
    })

# ---------------------------------------------------------------------
# Resumen con IA
# ---------------------------------------------------------------------
@routes_blueprint.post("/ai_summary")
def ai_summary():
    """Genera un resumen textual de tendencias usando IA."""

    content = request.json or {}
    data = content.get("data", [])

    if not data:
        return jsonify({"summary": "No hay datos para generar resumen"}), 400

    # Normalización segura de datos
    cleaned_data = [
        {
            "trend": d.get("trend"),
            "country": d.get("country"),
            "tweet_count": d.get("tweet_count", 0),
        }
        for d in data
        if d.get("trend") and d.get("country")
    ]

    if not cleaned_data:
        return jsonify({"summary": "Datos insuficientes para análisis"}), 400

    # Agrupación por tendencia
    aggregated = {}
    for d in cleaned_data:
        key = d["trend"].lower().strip()
        aggregated.setdefault(key, {
            "trend": d["trend"],
            "countries": set(),
            "tweet_count": 0,
        })

        aggregated[key]["countries"].add(d["country"])
        aggregated[key]["tweet_count"] += d["tweet_count"]

    aggregated_list = [
        {
            "trend": v["trend"],
            "country": ", ".join(list(v["countries"])[:3]),
            "tweet_count": v["tweet_count"],
        }
        for v in aggregated.values()
    ]

    top_data = sorted(
        aggregated_list,
        key=lambda x: x["tweet_count"],
        reverse=True,
    )[:30]

    trends_text = "\n".join(
        f"{d['trend']} ({d['country']}): {d['tweet_count']} tweets"
        for d in top_data
    )

    prompt = (
        "Genera un resumen conciso de las tendencias de Twitter usando SOLO texto plano. "
        "No uses tablas, Markdown, listas numeradas ni viñetas. "
        "Enfócate en los patrones principales y temas más relevantes. "
        "Describe únicamente los temas dominantes, patrones generales y posibles contextos relevantes. "
        "Debe tener máximo 200 palabras, si son menos, mejor"
        f"Datos:\n{trends_text}\nResumen:"
    )

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
        )

        summary = response.choices[0].message.content.strip()

    except Exception as e:
        print("Error con GroqCloud:", e)
        summary = "Error generando resumen con IA"

    return jsonify({"summary": summary})