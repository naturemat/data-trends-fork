"""Flask route handlers for trends metrics API."""

"""Flask route handlers for trends metrics API."""

import os
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, render_template
from app.models import Trend
from openai import OpenAI
from dateutil import parser

# ---------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------
# Ya no necesitamos definir prefijos aquí, __init__.py lo hace por nosotros.
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
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000")

@routes_blueprint.get("/config")
def get_config():
    """Devuelve configuración pública para el frontend."""
    return jsonify({
        "api_base": API_BASE_URL
    })

# ---------------------------------------------------------------------
# Frontend (Esta ruta raíz NO lleva prefijo /api usualmente, pero
# si el blueprint tiene prefijo, esto será /api/. 
# Si esto sirve el HTML, debería estar en otro blueprint, pero 
# por ahora lo dejaremos así para no romper más cosas).
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
    
    if not date_from_raw or not date_to_raw:
        query = {"pais": pais} if (pais and pais != "all") else {}
        latest = Trend.collection.find_one(query, sort=[("scraped_at", -1)])
        
        base_date = latest["scraped_at"] if latest else datetime.utcnow()
        
        dt_from = base_date.replace(hour=0, minute=0, second=0, microsecond=0)
        dt_to = base_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        try:
            dt_from = parser.parse(date_from_raw)
            dt_to = parser.parse(date_to_raw)
            
        except Exception:
            raise ValueError("Formato de fecha inválido. Se esperaba ISO 8601 o YYYY-MM-DD")

    if dt_from > dt_to:
        raise ValueError("La fecha de inicio no puede ser posterior a la de fin.")

    return {
        "pais": pais if (pais and pais != "all") else None,
        "from": dt_from,
        "to": dt_to
    }

# ---------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------
# CORREGIDO: Quitamos /api porque __init__.py ya lo pone
@routes_blueprint.get("/last_update")
def last_update():
    # Obtenemos el último documento
    docs = Trend.find_all(limit=1)

    if not docs:
        return jsonify({"last_update": None})

    last_doc = docs[0]
    scraped_at = last_doc.get("scraped_at")

    # Convertimos a ISO 8601 en UTC con Z
    if scraped_at and isinstance(scraped_at, datetime):
        # Asegurarnos que está en UTC
        if scraped_at.tzinfo is None:
            scraped_at = scraped_at.replace(tzinfo=timezone.utc)
        scraped_at_str = scraped_at.isoformat().replace("+00:00", "Z")
    else:
        scraped_at_str = None

    return jsonify({"last_update": scraped_at_str})


# ---------------------------------------------------------------------
# RUTA PRINCIPAL (LA QUE FALTABA)
# ---------------------------------------------------------------------
@routes_blueprint.get("/trends")
def get_trends():
    """
    Ruta principal que busca el test y el frontend.
    Devuelve las tendencias actuales.
    """
    try:
        # Reutilizamos la lógica de métricas o hacemos una búsqueda simple
        # Para que pase el test rápido, devolvemos activity o find_all
        params = parse_time_range(request)
        
        # Usamos aggregate_activity como default para la lista principal
        data = Trend.aggregate_activity(
            pais=params["pais"],
            dt_from=params["from"],
            dt_to=params["to"],
            granularity="hour"
        )
        return jsonify(data)
    except Exception as e:
         return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------
# Métricas Específicas
# ---------------------------------------------------------------------
# CORREGIDO: Quitamos /api de todas las rutas abajo

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
            "params": {
                "pais": params["pais"] or "all",
                "desde": params["from"].isoformat(),
                "hasta": params["to"].isoformat()
            },
            "data": data
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@routes_blueprint.get("/metrics/spread")
def spread_metric():
    limit = request.args.get("limit", default=50, type=int)
    pais = request.args.get("pais", default="worldwide")

    dt_to = datetime.now()
    dt_from = datetime(dt_to.year, dt_to.month, dt_to.day)

    from_str = request.args.get("date_from") or request.args.get("from")
    to_str = request.args.get("date_to") or request.args.get("to")

    if from_str and to_str:
        try:
            dt_from = datetime.fromisoformat(from_str) if 'T' in from_str else datetime.strptime(from_str, "%Y-%m-%d")
            dt_to = datetime.fromisoformat(to_str) if 'T' in to_str else datetime.strptime(to_str, "%Y-%m-%d")
            
            if 'T' not in to_str:
                dt_to = dt_to.replace(hour=23, minute=59, second=59)
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido"}), 400

    data = Trend.aggregate_spread(
        dt_from=dt_from,
        dt_to=dt_to,
        pais=pais,
        limit=limit
    )

    return jsonify({
        "desde": dt_from.isoformat(),
        "hasta": dt_to.isoformat(),
        "pais_consultado": pais,
        "data": data
    })

@routes_blueprint.post("/ai_summary")
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
            model="openai/gpt-oss-120b", 
            messages=[
                {"role": "system", "content": "Eres un narrador de noticias digitales que habla de forma clara y sencilla."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7, 
            max_tokens=800  
        )
        summary = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error AI: {e}")
        summary = "No se pudo generar el análisis detallado. Por favor, verifica la conexión con el servicio de inteligencia artificial."

    return jsonify({"summary": summary})