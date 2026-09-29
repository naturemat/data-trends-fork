"""MongoDB document models."""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
from app.db import db

# Zona horaria de referencia del proyecto (Ecuador, UTC-5).
#
# El dato crudo se guarda siempre en UTC, que es como Mongo lo interpreta.
# Los cortes por dia y por hora se hacen en esta zona para que el dashboard
# trama "el dialocal" y no el dia de UTC, y routes.py convierte a UTC con el
# mismo desplazamiento. Antes estos dos valores estaban escritos a mano en
# tres archivos distintos, por lo que cualquier cambio podia descuadrarlos.
DISPLAY_TZ = "-05:00"
DISPLAY_TZ_OFFSET = timedelta(hours=5)
# Para convertir a esa zona en Python hace falta un timedelta, no el string
# que usa Mongo en $dateTrunc.
DISPLAY_TZINFO = timezone(-DISPLAY_TZ_OFFSET)

# Se aplica al arrancar. Las agregaciones del dashboard filtran siempre por
# pais y scraped_at, y sin estos indices cada peticion recorre la coleccion
# entera. Es idempotente, asi que se puede llamar en cada despliegue.
INDEXES = [
    {"pais": 1, "scraped_at": -1},
    {"scraped_at": -1},
    {"tendencia": 1},
]


def ensure_indexes():
    """Crea los indices que necesitan las agregaciones, si no existen."""
    for keys in INDEXES:
        db.trends.create_index(keys)


def country_filter(pais):
    """Devuelve el filtro de pais para una agregacion.

    "all", "worldwide" y los valores vacios significan "sin filtro de pais", asi
    que devuelven un filtro vacio. Antes se hacia {"pais": pais} siempre, lo que
    hacia que pais="all" buscara un pais llamado literalmente "all" y devolviera
    vacio siempre, ya que ningun documento se guarda con ese valor.
    """
    if not pais or pais in ("all", "worldwide"):
        return {}
    return {"pais": pais}


def serialize_bucket_timestamp(value):
    """Convierte el _id de un bucket de $dateTrunc en texto ISO-8601.

    $dateTrunc con timezone devuelve un datetime que YA trae el desplazamiento
    (-05:00). Anadirle "Z" al final producia "...-05:00Z", que no es una fecha
    valida: en el front caia en Invalid Date y se rompia el eje del grafico de
    actividad.
    """
    return value.isoformat() if isinstance(value, datetime) else value


class Trend:
    """Modelo base para tendencias de Twitter."""

    collection = db.trends

    # ---------- CREACIÓN ----------

    @staticmethod
    def create_document(
        tendencia: str,
        numeroDeTwits: Optional[int] = None,
        pais: str = "worldwide"
    ) -> Dict:
        # scanned_at se guarda en UTC de forma explicita. Antes se usaba
        # datetime.now(), que es la hora local del servidor: si el servidor
        # no estaba en UTC el dato quedaba corrido y todas las graficas del
        # dashboard se desplazaban sin que nada fallara.
        scraped_at = datetime.now(timezone.utc)
        local = scraped_at.astimezone(DISPLAY_TZINFO)

        return {
            "fecha": local.strftime("%Y-%m-%d"),
            "hora": local.strftime("%H:%M:%S"),
            "tendencia": tendencia,
            "numeroDeTwits": numeroDeTwits,
            "pais": pais,
            "scraped_at": scraped_at
        }

    # ---------- CONSULTAS BÁSICAS ----------

    @classmethod
    def find_all(cls, limit: Optional[int] = None) -> List[Dict]:
        cursor = cls.collection.find().sort("scraped_at", -1)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    # ---------- METRICAS PARA EL FRONT ----------
    @classmethod
    def aggregate_activity(cls, pais, dt_from, dt_to, granularity="hour"):
        """
        Calcula la actividad de tendencias, midiendo específicamente cuántas tendencias
        NUEVAS aparecen en cada intervalo de tiempo comparadas con todo lo visto
        previamente en el rango seleccionado.
        """
        if granularity not in ("hour", "day"):
            raise ValueError("granularity debe ser 'hour' o 'day'")

        match = {"scraped_at": {"$gte": dt_from, "$lte": dt_to}}

        match.update(country_filter(pais))

        pipeline = [
            {
                "$match": match
            },
            {
                "$group": {
                    "_id": {
                        "$dateTrunc": {
                            "date": "$scraped_at", 
                            "unit": granularity,
                            "timezone": DISPLAY_TZ
                        }
                    },
                    # Agrupamos todos los nombres de tendencias de este bloque temporal
                    "trends_set": {"$addToSet": "$tendencia"}
                }
            },
            {"$sort": {"_id": 1}}
        ]

        result = list(cls.collection.aggregate(pipeline))

        processed_data = []
        # Usamos este set para recordar TODO lo que ya hemos contado como "nuevo"
        trends_seen_so_far = set()

        for i, r in enumerate(result):
            current_trends = set(r.get("trends_set", []))
            
            # En el primer registro del rango (ej. las 00:00), todas son "nuevas"
            if i == 0:
                new_trends_count = len(current_trends)
                trends_seen_so_far.update(current_trends)
            else:
                # Lógica de Diferencia:
                # Tendencias de esta hora que NO han aparecido en ninguna de las horas previas
                new_trends = current_trends - trends_seen_so_far
                new_trends_count = len(new_trends)
                
                # Actualizamos nuestro registro histórico con los nuevos hallazgos
                trends_seen_so_far.update(new_trends)

            # Preparamos el objeto para el frontend
            timestamp_val = r["_id"]
            processed_data.append({
                # $dateTrunc con timezone devuelve un valor que ya trae el
                # desplazamiento (-05:00). Anadirle "Z" al final producia
                # "2026-02-20T15:00:00-05:00Z", que no es una fecha valida:
                # en el front caia en Invalid Date y se rompia el eje del
                # grafico de actividad.
                "timestamp": serialize_bucket_timestamp(timestamp_val),
                "total_trends_in_period": len(current_trends), # Cuántas había en esa hora
                "new_trends": new_trends_count                # Cuántas son estrictamente nuevas
            })

        return processed_data

    @classmethod
    def aggregate_persistence(
        cls,
        dt_from: datetime,
        dt_to: datetime,
        pais: Optional[str] = "worldwide",
        granularity: str = "hour",
        limit: int = 20
    ) -> List[Dict]:

        if granularity not in ("hour", "day"):
            raise ValueError("granularity must be 'hour' or 'day'")

        match = {
            "scraped_at": {"$gte": dt_from, "$lte": dt_to}
        }

        match.update(country_filter(pais))

        pipeline = [
            {"$match": match},
            {
                "$addFields": {
                    "time_unit": {
                        # Cambio: Agregamos timezone para definir el bloque de tiempo local
                        "$dateTrunc": {
                            "date": "$scraped_at", 
                            "unit": granularity,
                            "timezone": DISPLAY_TZ
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": "$tendencia",
                    "time_units": {"$addToSet": "$time_unit"},
                    "countries": {"$addToSet": "$pais"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "trend": "$_id",
                    "appearances": {"$size": "$time_units"},
                    "time_units_active": {"$size": "$time_units"},
                    "countries": 1,
                    "raw_time_units": "$time_units" 
                }
            },
            {"$sort": {"appearances": -1}},
            {"$limit": limit}
        ]

        result = list(cls.collection.aggregate(pipeline))
        
        for r in result:
            if "raw_time_units" in r:
                # El isoformat ahora incluirá el sufijo -05:00, avisando al front que ya está ajustado
                r["raw_time_units"] = [t.isoformat() for t in r["raw_time_units"]]
                
        return result
    
    @classmethod
    def aggregate_spread(
        cls,
        dt_from: datetime,
        dt_to: datetime,
        pais: str = "worldwide",
        limit: int = 50,
    ) -> List[Dict]:
        """
        Analiza el alcance global/regional/local de las tendencias.
        Nueva lógica: 
        - GLOBAL: Si está en 'worldwide' O aparece en >= 10 países.
        - REGIONAL: Si aparece en >= 3 países.
        - LOCAL: Resto de casos.
        """
        
        match_time = {
            "scraped_at": {"$gte": dt_from, "$lte": dt_to}
        }

        # 1. Identificar tendencias presentes en el país seleccionado
        filtro_local = {**match_time, **country_filter(pais)}
        tendencias_en_este_pais = cls.collection.distinct("tendencia", filtro_local)

        if not tendencias_en_este_pais:
            return []

        pipeline = [
            {
                "$match": {
                    **match_time,
                    "tendencia": {"$in": tendencias_en_este_pais}
                }
            },
            {
                "$group": {
                    "_id": "$tendencia",
                    "locations": {"$addToSet": "$pais"},
                    "appearances": {"$sum": 1}
                }
            },
            {
                "$addFields": {
                    "in_worldwide": {"$in": ["worldwide", "$locations"]},
                    "countries": {
                        "$filter": {
                            "input": "$locations",
                            "as": "p",
                            "cond": {"$ne": ["$$p", "worldwide"]}
                        }
                    }
                }
            },
            {
                "$addFields": {
                    "countries_count": {"$size": "$countries"},
                    "scope": {
                        "$cond": [
                            # REGLA GLOBAL: Aparece en Worldwide O tiene 10 o más países
                            {"$or": [
                                {"$eq": ["$in_worldwide", True]}, 
                                {"$gte": [{"$size": "$countries"}, 10]}
                            ]}, 
                            "global",
                            # REGLA REGIONAL: 3 o más locaciones en total
                            {"$cond": [
                                {"$gte": [{"$size": "$locations"}, 3]}, 
                                "regional", 
                                "local"
                            ]}
                        ]
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "trend": "$_id",
                    "scope": 1,
                    "countries": 1,
                    "countries_count": 1,
                    "in_worldwide": 1,
                    "appearances": 1
                }
            },
            {"$sort": {"countries_count": -1, "appearances": -1}},
            {"$limit": limit}
        ]

        return list(cls.collection.aggregate(pipeline))
    
    @classmethod
    def get_dashboard_summary(cls, pais, dt_from, dt_to, granularity="hour"):
        # 1. Obtenemos las tendencias únicas que aparecen en el país seleccionado
        filtro_local = {"scraped_at": {"$gte": dt_from, "$lte": dt_to}}

        filtro_local.update(country_filter(pais))

        tendencias_en_este_pais = cls.collection.distinct("tendencia", filtro_local)

        if not tendencias_en_este_pais:
            return {"total_unique": 0, "total_global": 0, "total_paises": 0}

        # 2. Pipeline para calcular métricas de esas tendencias específicas
        pipeline = [
            {
                "$match": {
                    "scraped_at": {"$gte": dt_from, "$lte": dt_to},
                    "tendencia": {"$in": tendencias_en_este_pais}
                }
            },
            {
                "$group": {
                    "_id": "$tendencia",
                    "locations": {"$addToSet": "$pais"}
                }
            },
            {
                "$addFields": {
                    "in_worldwide": {"$in": ["worldwide", "$locations"]},
                    # Filtramos 'worldwide' para contar solo países reales
                    "real_countries": {
                        "$filter": {
                            "input": "$locations",
                            "as": "p",
                            "cond": {"$ne": ["$$p", "worldwide"]}
                        }
                    }
                }
            },
            {
                "$addFields": {
                    "is_global": {
                        "$or": [
                            {"$eq": ["$in_worldwide", True]},
                            {"$gte": [{"$size": "$real_countries"}, 10]}
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_unicas": {"$sum": 1},
                    "total_globales": {"$sum": {"$cond": ["$is_global", 1, 0]}},
                    "all_locations": {"$push": "$real_countries"}
                }
            }
        ]

        result = list(cls.collection.aggregate(pipeline))
        if not result:
            return {"total_unique": 0, "total_global": 0, "total_paises": 0}

        # Aplanamos la lista de países reales para el conteo de la Card
        paises_reales = {p for sublist in result[0]["all_locations"] for p in sublist}
        
        # Lógica solicitada: 
        # Si filtramos por un país específico, 'Paises analizados' debería ser ese país (1)
        # Si es worldwide o "all", debería ser el conteo de todos los países donde hay datos.
        count_paises = 1 if country_filter(pais) else len(paises_reales)

        return {
            "total_unique": result[0]["total_unicas"],
            "total_global": result[0]["total_globales"],
            "total_paises": count_paises
        }
    
    @classmethod
    def aggregate_survival_stats(cls, pais, dt_from, dt_to, granularity="hour"):
        # Decidimos los puntos de corte (bins) basados siempre en HORAS
        # pero ajustados a los labels que el usuario espera ver.
        
        diff_days = (dt_to - dt_from).days
        
        if diff_days <= 2:
            # Escala de corto plazo: 0h, 3h, 9h, 24h
            bins = [0, 3, 9, 24]
            labels = ["Fugaz (<3h)", "Activa (3-8h)", "Persistente (9-23h)", "Inmortal (>=24h)"]
        else:
            # Escala de largo plazo: convertimos los días de tus labels a horas
            # Efímera: < 24h
            # Estable: 24h a 71h (1-2 días)
            # Semanal: 72h a 167h (3-6 días)
            # Histórica: >= 168h (7+ días)
            bins = [0, 24, 72, 168]
            labels = ["Efímera (<1d)", "Estable (1-2d)", "Semanal (3-6d)", "Histórica (>=7d)"]

        match = {"scraped_at": {"$gte": dt_from, "$lte": dt_to}}

        match.update(country_filter(pais))

        pipeline = [
            {"$match": match},
            {
                "$group": {
                    "_id": {"$trim": {"input": "$tendencia"}},
                    # USAMOS SIEMPRE "hour" para la métrica interna de supervivencia
                    "horas_vivas": {
                        "$addToSet": {
                            "$dateTrunc": {
                                "date": "$scraped_at",
                                "unit": "hour",
                                "timezone": DISPLAY_TZ
                            }
                        }
                    }
                }
            },
            {
                "$project": {
                    "trend_name": "$_id",
                    "total_hours": {"$size": "$horas_vivas"} 
                }
            },
            {"$sort": {"total_hours": -1}}, 
            {
                "$bucket": {
                    "groupBy": "$total_hours",
                    "boundaries": bins,
                    "default": "Superior",
                    "output": { 
                        "count": { "$sum": 1 },
                        "trends": { "$push": "$trend_name" }
                    }
                }
            }
        ]
        
        raw_data = list(cls.collection.aggregate(pipeline))
        
        # Formateo final (idéntico al anterior)
        formatted = []
        for i, b in enumerate(bins):
            label = labels[i]
            item_data = next((x for x in raw_data if x["_id"] == b), {"count": 0, "trends": []})
            
            count = item_data["count"]
            trends = item_data["trends"]

            if i == len(bins) - 1:
                sup = next((x for x in raw_data if x["_id"] == "Superior"), {"count": 0, "trends": []})
                count += sup["count"]
                trends += sup["trends"]

            formatted.append({
                "label": label,
                "count": count,
                "topTrends": trends[:3]
            })
        
        return formatted