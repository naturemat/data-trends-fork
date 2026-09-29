"""Flask route handlers for trends metrics API."""

import json
import logging
import os
from datetime import datetime, timedelta

from dateutil import parser
from flask import Blueprint, request, jsonify, render_template
from openai import OpenAI

from app.models import Trend

# ---------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------
routes_blueprint = Blueprint("routes", __name__)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Configuracion IA (Groq / OpenAI compatible)
# ---------------------------------------------------------------------
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama-3.3-70b-versatile"

_clients = {}


def get_groq_client(env_var):
    """Devuelve un cliente de Groq, creandolo la primera vez que se usa.

    Se construye bajo demanda y no al importar el modulo para que la aplicacion
    pueda arrancar aunque las llaves de IA no esten configuradas; el error sale
    solo cuando se llama a un endpoint que si las necesita.
    """
    if env_var not in _clients:
        api_key = os.environ.get(env_var)
        if not api_key:
            raise RuntimeError("Falta la variable de entorno " + env_var)
        _clients[env_var] = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)
    return _clients[env_var]

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
# IA Summary
# ---------------------------------------------------------------------
@routes_blueprint.post("/api/ai_summary")
def ai_summary():
    content = request.get_json(silent=True) or {}
    # Ahora recibiremos los datos de persistencia (frecuencia)
    data = content.get("data") or []
    pais_nombre = content.get("pais_nombre", "Global")

    if not data:
        return jsonify({"summary": "No hay datos suficientes para el análisis."}), 400

    # Tomamos el Top 15-20 para no saturar el prompt pero tener calidad
    top_data = data[:15] 
    
    # Construimos el contexto basado en PERSISTENCIA (apariciones)
    context_text = "\n".join([
        f"- TENDENCIA: {d.get('trend', 'N/A')} | "
        f"FRECUENCIA: {d.get('appearances', 0)} registros detectados | "
        f"RELEVANCIA: {'Alta' if d.get('appearances', 0) > 10 else 'Media'}"
        for d in top_data
    ])

    enfoque_geografico = f"enfocándote específicamente en lo que está ocurriendo en {pais_nombre}" if pais_nombre != "Worldwide" else "con una perspectiva global"

    prompt = (
        f"Eres un periodista experto en análisis de datos de redes sociales. Analiza las tendencias más persistentes en {pais_nombre} {enfoque_geografico}. "
        "Los datos muestran temas que se han mantenido activos durante múltiples chequeos, lo que indica un interés sostenido. "
        "ESTRUCTURA (Texto plano, sin asteriscos, sin negritas):"
        f"1. EL TEMA EN {pais_nombre.upper()}: ¿Cuál es la conversación dominante y por qué se mantiene en el tiempo? "
        "2. CONTEXTO LOCAL: ¿Qué dice esto de la audiencia actual? "
        "3. EL MOTIVO DETRÁS: Explica el origen real de esta popularidad basándote en los nombres de las tendencias (deportes, política, etc.). "
        "REGLAS: Texto plano, lenguaje profesional pero sencillo, entre 200 y 300 palabras."
        f"\nDATOS DE PERSISTENCIA:\n{context_text}"
    )

    try:
        response = get_groq_client("GROQCLOUD_API_KEY").chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "Eres un analista de opinión pública y tendencias digitales."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        summary = response.choices[0].message.content.strip()
        # Limpieza extra para asegurar texto plano sin Markdown
        summary = summary.replace("*", "").replace("#", "")
    except Exception as e:
        log.exception("Error en el endpoint /api/ai_summary")
        return jsonify({"summary": f"Error en la IA: {str(e)}"}), 500

    return jsonify({"summary": summary})
    
@routes_blueprint.get('/api/metrics/summary')
def get_summary():
    try:
        params = parse_time_range(request)
        granularity = request.args.get('granularity', 'hour')

        summary = Trend.get_dashboard_summary(
            pais=params["pais"], 
            dt_from=params["from"], 
            dt_to=params["to"], 
            granularity=granularity
        )
        return jsonify(summary)
    except Exception as e:
        log.exception("Error en el endpoint /api/metrics/summary")
        return jsonify({"error": str(e)}), 500
    
@routes_blueprint.get("/api/metrics/survival")
def metrics_survival():
    try:
        params = parse_time_range(request)
        granularity = request.args.get("granularity", "hour")
        
        data = Trend.aggregate_survival_stats(
            pais=params["pais"],
            dt_from=params["from"],
            dt_to=params["to"],
            granularity=granularity
        )
        return jsonify({"data": data})
    except Exception as e:
        log.exception("Error en el endpoint /api/metrics/survival")
        return jsonify({"error": str(e)}), 500
    
# ---------------------------------------------------------------------
# Clasificación
# ---------------------------------------------------------------------
@routes_blueprint.get("/api/metrics/ai_classification")
def ai_classification():
    try:
        # 1. Parámetros de tiempo y país
        params = parse_time_range(request)
        
        # 2. Obtenemos el Top 50 de persistencia
        top_trends_data = Trend.aggregate_persistence(
            dt_from=params["from"], 
            dt_to=params["to"],
            pais=params["pais"], 
            limit=50
        )

        if not top_trends_data:
            return jsonify({"data": {}})

        # Extraemos solo los nombres de las tendencias
        trends_list = [d["trend"] for d in top_trends_data]

        # 3. Prompt para devolver listas de tendencias
        prompt = (
            f"Analiza estas tendencias de Twitter en {params['pais']} y clasifícalas "
            "EXCLUSIVAMENTE en estas categorías: 'Politica y gobierno', 'Deportes', "
            "'Entretenimiento', 'Tecnología', 'Economia', 'Otros'.\n"
            "Devuelve un objeto JSON donde cada llave sea el nombre de la categoría "
            "y el valor sea una LISTA con los nombres de las tendencias que pertenecen a ella.\n"
            "Ejemplo: {'Deportes': ['#Champions', 'Messi'], 'Tecnología': ['iPhone15'], ...}\n"
            f"LISTA DE TENDENCIAS: {', '.join(trends_list)}"
        )

        # 4. Llamada a Groq con la segunda llave (GROQCLOUD_API_KEY_ALT)
        response = get_groq_client("GROQCLOUD_API_KEY_ALT").chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "Eres un clasificador preciso. Responde solo con el JSON solicitado."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1 # Muy bajo para evitar alucinaciones
        )

        # 5. Parsear y devolver
        classification_json = json.loads(response.choices[0].message.content)

        # Retornamos el JSON tal cual lo entrega la IA (Categoría -> Lista de Tendencias)
        return jsonify(classification_json)

    except Exception as e:
        log.exception("Error en el endpoint /api/metrics/ai_classification")
        return jsonify({"error": str(e)}), 500