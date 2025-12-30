"""Flask route handlers for trends metrics API."""
import os
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, render_template
from app.models import Trend
from openai import OpenAI
from dateutil import parser

# Blueprint
routes_blueprint = Blueprint("routes", __name__)

# Configuración IA
GROQCLOUD_API_KEY = os.environ.get("GROQCLOUD_API_KEY")
client = OpenAI(
    api_key=GROQCLOUD_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000")

@routes_blueprint.get("/config")
def get_config():
    return jsonify({"api_base": API_BASE_URL})

@routes_blueprint.get("/")
def index():
    return render_template("index.html")

# --- CORRECCIÓN CRÍTICA DE FECHAS ---
def parse_time_range(req):
    pais = req.args.get("pais", "worldwide")
    # Forzar minúsculas para evitar problemas de filtro
    if pais:
        pais = pais.lower()
        
    date_from_raw = req.args.get("date_from")
    date_to_raw = req.args.get("date_to")
    
    # Si no llegan fechas, usamos el día de hoy completo
    if not date_from_raw or not date_to_raw:
        dt_to = datetime.now(timezone.utc)
        dt_from = dt_to.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        try:
            # Parseamos las fechas
            dt_from = parser.parse(date_from_raw)
            dt_to = parser.parse(date_to_raw)
            
            # --- TRUCO DE MAGIA: Si la fecha fin es "00:00", la empujamos al final del día ---
            # Verificamos si la hora es 00:00:00 (que es el default cuando no se envía hora)
            if dt_to.hour == 0 and dt_to.minute == 0 and dt_to.second == 0:
                dt_to = dt_to.replace(hour=23, minute=59, second=59, microsecond=999999)
                
        except Exception:
            dt_to = datetime.now(timezone.utc)
            dt_from = dt_to.replace(hour=0, minute=0, second=0)
            
    return {
        "pais": pais if (pais and pais != "all") else None,
        "from": dt_from,
        "to": dt_to
    }

# --- RUTAS ---

@routes_blueprint.get("/last_update")
def last_update():
    docs = Trend.find_all(limit=1)
    if not docs:
        return jsonify({"last_update": None})
    last_doc = docs[0]
    scraped_at = last_doc.get("scraped_at")
    if scraped_at and isinstance(scraped_at, datetime):
        if scraped_at.tzinfo is None:
            scraped_at = scraped_at.replace(tzinfo=timezone.utc)
        scraped_at_str = scraped_at.isoformat().replace("+00:00", "Z")
    else:
        scraped_at_str = None
    return jsonify({"last_update": scraped_at_str})

@routes_blueprint.get("/trends")
def get_trends():
    try:
        params = parse_time_range(request)
        data = Trend.aggregate_activity(
            pais=params["pais"],
            dt_from=params["from"],
            dt_to=params["to"],
            granularity="hour"
        )
        return jsonify(data)
    except Exception as e:
         return jsonify({"error": str(e)}), 500

@routes_blueprint.get("/metrics/activity")
def metrics_activity():
    try:
        params = parse_time_range(request)
        granularity = request.args.get("granularity", "hour")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    data = Trend.aggregate_activity(
        pais=params["pais"],
        dt_from=params["from"],
        dt_to=params["to"],
        granularity=granularity
    )
    return jsonify({
        "pais": params["pais"],
        "granularity": granularity,
        "desde": params["from"].isoformat(),
        "hasta": params["to"].isoformat(),
        "data": data
    })

@routes_blueprint.get("/metrics/persistence")
def persistence_metric():
    try:
        params = parse_time_range(request)
        limit = request.args.get("limit", default=20, type=int)
        granularity = request.args.get("granularity", "hour")

        data = Trend.aggregate_persistence(
            dt_from=params["from"],
            dt_to=params["to"],
            pais=params["pais"],
            granularity=granularity,
            limit=limit
        )
        return jsonify({
            "status": "success",
            "data": data
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@routes_blueprint.get("/metrics/intensity")
def intensity_metric():
    try:
        params = parse_time_range(request)
        limit = request.args.get("limit", default=20, type=int)

        data = Trend.aggregate_intensity(
            dt_from=params["from"],
            dt_to=params["to"],
            pais=params["pais"],
            limit=limit
        )
        return jsonify({
            "status": "success",
            "data": data
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@routes_blueprint.get("/metrics/spread")
def spread_metric():
    limit = request.args.get("limit", default=50, type=int)
    # Reutilizamos la lógica robusta de fechas
    try:
        params = parse_time_range(request)
    except:
        return jsonify({"error": "Fechas inválidas"}), 400

    data = Trend.aggregate_spread(
        dt_from=params["from"],
        dt_to=params["to"],
        pais=params["pais"],
        limit=limit
    )
    return jsonify({
        "desde": params["from"].isoformat(),
        "hasta": params["to"].isoformat(),
        "pais_consultado": params["pais"],
        "data": data
    })

@routes_blueprint.post("/ai_summary")
def ai_summary():
    return jsonify({"summary": "IA desactivada temporalmente para debug."})