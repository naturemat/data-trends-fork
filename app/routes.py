"""Flask route handlers for trends metrics API."""

import os
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, render_template
from app.models import Trend
from openai import OpenAI
from dateutil import parser

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
# Configuración general
# ---------------------------------------------------------------------
API_BASE_URL = os.getenv("API_BASE_URL", "")

@routes_blueprint.get("/api/config")
def get_config():
    """Devuelve configuración pública para el frontend."""
    return jsonify({
        "api_base": API_BASE_URL
    })

# ---------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------
@routes_blueprint.get("/")
def index():
    return render_template("index.html")

# ---------------------------------------------------------------------
# Utilidad: parseo de rango de fechas y horas
# ---------------------------------------------------------------------
def parse_time_range(req):
    pais = req.args.get("pais", "worldwide")
    date_from_raw = req.args.get("date_from")
    date_to_raw = req.args.get("date_to")
    
    # Definimos el ajuste: Ecuador está 5 horas detrás de UTC
    # Para consultar la DB (UTC), sumamos 5 horas a la hora local deseada
    offset = timedelta(hours=5)
    
    if not date_from_raw or not date_to_raw:
        query = {"pais": pais} if (pais and pais != "all") else {}
        latest = Trend.collection.find_one(query, sort=[("scraped_at", -1)])
        
        # Dentro de if not date_from_raw:
        base_date_utc = latest["scraped_at"] if latest else datetime.utcnow()
        # 1. Convertimos a Ecuador primero
        base_date_ec = base_date_utc - timedelta(hours=5)

        # 2. Seteamos inicio y fin del día NATURAL de Ecuador
        dt_from_local = base_date_ec.replace(hour=0, minute=0, second=0, microsecond=0)
        dt_to_local = base_date_ec.replace(hour=23, minute=59, second=59, microsecond=999999)

        # 3. Enviamos a la DB sumando 5 para buscar en UTC
        dt_from = dt_from_local + timedelta(hours=5)
        dt_to = dt_to_local + timedelta(hours=5)
    else:
        dt_from = parser.parse(date_from_raw).replace(tzinfo=None) + offset
        dt_to = parser.parse(date_to_raw).replace(tzinfo=None) + offset

    return {"pais": pais, "from": dt_from, "to": dt_to}

# ---------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------
@routes_blueprint.get("/api/last_update")
def last_update():
    docs = Trend.find_all(limit=1)
    if not docs:
        return jsonify({"last_update": None})

    last_doc = docs[0]
    scraped_at = last_doc.get("scraped_at")

    if scraped_at and isinstance(scraped_at, datetime):
        scraped_at_str = scraped_at.isoformat() + "Z"
    else:
        scraped_at_str = None

    return jsonify({"last_update": scraped_at_str})

# ---------------------------------------------------------------------
# (Placeholder) Métricas
# ---------------------------------------------------------------------
@routes_blueprint.get("/api/metrics/activity")
def metrics_activity():
    """
    Actividad temporal de tendencias
    - por hora
    - por día
    """

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

@routes_blueprint.get("/api/metrics/persistence")
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
            "params": {
                "pais": params["pais"] or "all",
                "desde": params["from"].isoformat(),
                "hasta": params["to"].isoformat(),
                "granularity": granularity
            },
            "data": data
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@routes_blueprint.get("/api/metrics/intensity")
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
            "params": {
                "pais": params["pais"] or "all",
                "desde": params["from"].isoformat(),
                "hasta": params["to"].isoformat()
            },
            "data": data
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@routes_blueprint.get("/api/metrics/spread")
def spread_metric():
    limit = request.args.get("limit", default=50, type=int)
    pais = request.args.get("pais", default="worldwide")
    offset = timedelta(hours=5)

    from_str = request.args.get("date_from") or request.args.get("from")
    to_str = request.args.get("date_to") or request.args.get("to")

    if from_str and to_str:
        try:
            # Sumamos el offset para buscar en la DB que es UTC
            dt_from = parser.parse(from_str).replace(tzinfo=None) + offset
            dt_to = parser.parse(to_str).replace(tzinfo=None) + offset
        except Exception:
            return jsonify({"error": "Formato de fecha inválido"}), 400
    else:
        # Por defecto: hoy en Ecuador (traducido a UTC para la DB)
        ahora_ec = datetime.utcnow() - offset
        dt_from = ahora_ec.replace(hour=0, minute=0, second=0, microsecond=0) + offset
        dt_to = ahora_ec.replace(hour=23, minute=59, second=59, microsecond=999999) + offset

    data = Trend.aggregate_spread(
        dt_from=dt_from,
        dt_to=dt_to,
        pais=pais,
        limit=limit
    )

    return jsonify({
        "desde": dt_from.isoformat() + ("Z" if dt_from.tzinfo == timezone.utc else ""),
        "hasta": dt_to.isoformat() + ("Z" if dt_to.tzinfo == timezone.utc else ""),
        "pais_consultado": pais,
        "data": data
    })

@routes_blueprint.post("/api/ai_summary")
def ai_summary():
    content = request.get_json(silent=True) or {}
    data = content.get("data") or []
    pais_nombre = content.get("pais_nombre", "Global")

    if not data:
        return jsonify({"summary": "No hay datos suficientes para el análisis."}), 400

    top_data = data[:20] 
    
    context_text = "\n".join([
        f"- TENDENCIA: {d['trend']} | ALCANCE: {d['scope']} | PAÍSES: {', '.join(d['countries'][:5])} ({d['countries_count']} en total)"
        for d in top_data
    ])
    enfoque_geografico = f"enfocándote específicamente en lo que está ocurriendo en {pais_nombre}" if pais_nombre != "Worldwide" else "con una perspectiva global"

    prompt = (
        f"Eres un periodista experto en tendencias. Analiza los siguientes datos {enfoque_geografico}. "
        "Tu objetivo es explicar qué le interesa a la gente en este lugar hoy. "
        
        "ESTRUCTURA (Texto plano):"
        f"1. EL TEMA EN {pais_nombre.upper()}: Resume la conversación principal de este lugar. "
        "2. CONTEXTO LOCAL: Explica por qué estos temas son relevantes para esta audiencia específica. "
        "3. EL MOTIVO DETRÁS: Explica por qué crees que estos temas son populares hoy (¿Hay un partido? ¿Es Navidad? ¿Hay elecciones?). "

        "REGLAS: Texto plano, lenguaje sencillo, entre 200 y 300 palabras."
        f"\nDATOS:\n{context_text}"
    )

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b", # O el modelo que prefieras
            messages=[
                {"role": "system", "content": "Eres un narrador de noticias digitales que habla de forma clara y sencilla."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7, # Un poco de creatividad para la interpretación del contexto
            max_tokens=800   # Espacio suficiente para un resumen detallado
        )
        summary = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error AI: {e}")
        summary = "No se pudo generar el análisis detallado. Por favor, verifica la conexión con el servicio de inteligencia artificial."

    return jsonify({"summary": summary})