"""Flask route handlers for trends metrics API."""

import os
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, render_template
from app.models import Trend
from openai import OpenAI
from dateutil import parser
from modules.embeddings import embedding_manager

# ---------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------
routes_blueprint = Blueprint("routes", __name__)

# ---------------------------------------------------------------------
# Configuración IA (Groq / OpenAI compatible)
# ---------------------------------------------------------------------
# Se ajusta para que coincida con el nombre en el archivo .env de AWS
GROQ_API_KEY = os.environ.get("GROQCLOUD_API_KEY")

client = OpenAI(
    api_key=GROQ_API_KEY,
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
    
    offset = timedelta(hours=5)
    
    if not date_from_raw or not date_to_raw:
        query = {"pais": pais} if (pais and pais != "all") else {}
        latest = Trend.collection.find_one(query, sort=[("scraped_at", -1)])
        
        base_date_utc = latest["scraped_at"] if latest else datetime.utcnow()
        base_date_ec = base_date_utc - offset

        dt_from_local = base_date_ec.replace(hour=0, minute=0, second=0, microsecond=0)
        dt_to_local = base_date_ec.replace(hour=23, minute=59, second=59, microsecond=999999)

        dt_from = dt_from_local + offset
        dt_to = dt_to_local + offset
    else:
        dt_from = parser.parse(date_from_raw).replace(hour=0, minute=0, second=0) + offset
        dt_to = parser.parse(date_to_raw).replace(hour=23, minute=59, second=59) + offset

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
# Métricas
# ---------------------------------------------------------------------
@routes_blueprint.get("/api/metrics/activity")
def metrics_activity():
    try:
        params = parse_time_range(request)
        granularity = request.args.get("granularity", "hour")
        data = Trend.aggregate_activity(
            pais=params["pais"],
            dt_from=params["from"],
            dt_to=params["to"],
            granularity=granularity
        )
        return jsonify({"data": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@routes_blueprint.get("/api/metrics/persistence")
def persistence_metric():
    try:
        params = parse_time_range(request)
        data = Trend.aggregate_persistence(
            dt_from=params["from"], dt_to=params["to"],
            pais=params["pais"], limit=20
        )
        return jsonify({"data": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@routes_blueprint.get("/api/metrics/intensity")
def intensity_metric():
    try:
        params = parse_time_range(request)
        data = Trend.aggregate_intensity(
            dt_from=params["from"], dt_to=params["to"],
            pais=params["pais"], limit=20
        )
        return jsonify({"data": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@routes_blueprint.get("/api/metrics/spread")
def spread_metric():
    try:
        params = parse_time_range(request)
        data = Trend.aggregate_spread(
            dt_from=params["from"], dt_to=params["to"],
            pais=params["pais"], limit=50
        )
        return jsonify({"data": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ---------------------------------------------------------------------
# IA Summary (CORRECCIÓN DEFINITIVA DE KEYERROR)
# ---------------------------------------------------------------------
@routes_blueprint.post("/api/ai_summary")
def ai_summary():
    content = request.get_json(silent=True) or {}
    data = content.get("data") or []
    pais_nombre = content.get("pais_nombre", "Global")

    if not data:
        return jsonify({"summary": "No hay datos suficientes para el análisis."}), 400

    top_data = data[:20] 
    
    # SE USA .get() PARA EVITAR EL KEYERROR 'scope' O 'countries'
    context_text = "\n".join([
        f"- TENDENCIA: {d.get('trend', 'N/A')} | "
        f"ALCANCE: {d.get('scope', 'Local')} | "
        f"PAÍSES: {', '.join(d.get('countries', [])[:5])} ({d.get('countries_count', 0)} en total)"
        for d in top_data
    ])

    enfoque_geografico = f"enfocándote específicamente en lo que está ocurriendo en {pais_nombre}" if pais_nombre != "Worldwide" else "con una perspectiva global"

    prompt = (
        f"Eres un periodista experto en tendencias. Analiza los siguientes datos {enfoque_geografico}. "
        "Tu objetivo es explicar qué le interesa a la gente en este lugar hoy. "
        "ESTRUCTURA (Texto plano):"
        f"1. EL TEMA EN {pais_nombre.upper()}: Resume la conversación principal. "
        "2. CONTEXTO LOCAL: Explica la relevancia para esta audiencia. "
        "3. EL MOTIVO DETRÁS: Explica el origen de la popularidad. "
        "REGLAS: Texto plano, lenguaje sencillo, entre 200 y 300 palabras."
        f"\nDATOS:\n{context_text}"
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Eres un narrador de noticias digitales claro y conciso."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        summary = response.choices[0].message.content.strip()
    except Exception as e:
        # Esto permite capturar si la API Key es rechazada o el modelo no está disponible
        print(f"Error crítico AI: {e}")
        return jsonify({"summary": f"Error en la IA: {str(e)}"}), 500

    return jsonify({"summary": summary})


# ---------------------------------------------------------------------
# Embeddings and Enrichment
# ---------------------------------------------------------------------
@routes_blueprint.post("/api/embeddings/search")
def embeddings_search():
    """Search for similar trends using semantic embeddings."""
    content = request.get_json(silent=True) or {}
    query = content.get("query", "").strip()

    if not query:
        return jsonify({"error": "Query text is required"}), 400

    try:
        results = embedding_manager.search_similar(query, top_k=10)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@routes_blueprint.get("/api/embeddings/enrich")
def embeddings_enrich():
    """Retrieve all trends with their enrichment data (topics)."""
    try:
        enriched_trends = embedding_manager.get_all_enriched_trends()
        return jsonify({"trends": enriched_trends})
    except Exception as e:
        return jsonify({"error": str(e)}), 500