"""MongoDB document models."""

from datetime import datetime
from typing import Optional, List, Dict
from app.db import db

class Trend:
    """Modelo base para tendencias de Twitter."""

    collection = db.trends

    def __init__(self, data: Dict):
        self.id = data.get("_id")
        self.fecha = data.get("fecha")
        self.hora = data.get("hora")
        self.tendencia = data.get("tendencia")
        self.numeroDeTwits = data.get("numeroDeTwits")
        self.pais = data.get("pais")
        self.scraped_at = data.get("scraped_at")

    # ---------- CREACIÓN ----------

    @staticmethod
    def create_document(
        tendencia: str,
        numeroDeTwits: Optional[int] = None,
        pais: str = "worldwide"
    ) -> Dict:
        now = datetime.now()
        return {
            "fecha": now.strftime("%Y-%m-%d"),
            "hora": now.strftime("%H:%M:%S"),
            "tendencia": tendencia,
            "numeroDeTwits": numeroDeTwits,
            "pais": pais,
            "scraped_at": now
        }

    @classmethod
    def insert_one(cls, document: Dict):
        return cls.collection.insert_one(document)

    # ---------- CONSULTAS BÁSICAS ----------

    @classmethod
    def find_all(cls, limit: Optional[int] = None) -> List[Dict]:
        cursor = cls.collection.find().sort("scraped_at", -1)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    @classmethod
    def find_by_country(
        cls,
        pais: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        cursor = cls.collection.find(
            {"pais": pais}
        ).sort("scraped_at", -1)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    @classmethod
    def find_by_date_range(
        cls,
        fecha_inicio: str,
        fecha_fin: str,
        pais: Optional[str] = None
    ) -> List[Dict]:
        query = {
            "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin}
        }

        if pais:
            query["pais"] = pais

        return list(
            cls.collection.find(query).sort("scraped_at", -1)
        )
    
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

        pipeline = [
            {
                "$match": {
                    "pais": pais,
                    "scraped_at": {"$gte": dt_from, "$lte": dt_to}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateTrunc": {
                            "date": "$scraped_at", 
                            "unit": granularity,
                            "timezone": "-05:00"
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
                "timestamp": timestamp_val.isoformat() + "Z" if isinstance(timestamp_val, datetime) else timestamp_val,
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

        if pais and pais != "all":
            match["pais"] = pais

        pipeline = [
            {"$match": match},
            {
                "$addFields": {
                    "time_unit": {
                        # Cambio: Agregamos timezone para definir el bloque de tiempo local
                        "$dateTrunc": {
                            "date": "$scraped_at",
                            "unit": granularity,
                            "timezone": "-05:00"
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
        filtro_local = {**match_time, "pais": pais} if pais and pais != "all" else match_time
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
        filtro_local = {
            "scraped_at": {"$gte": dt_from, "$lte": dt_to},
            "pais": pais
        }
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
        # Si es worldwide, debería ser el conteo de todos los países donde hay datos.
        count_paises = len(paises_reales) if pais == "worldwide" else 1

        return {
            "total_unique": result[0]["total_unicas"],
            "total_global": result[0]["total_globales"],
            "total_paises": count_paises
        }
    
    @classmethod
    def aggregate_synchrony_radar(cls, pais, dt_from, dt_to):
        pipeline = [
            # 1. Filtrar rango y solo el país seleccionado + worldwide
            {"$match": {
                "scraped_at": {"$gte": dt_from, "$lte": dt_to},
                "pais": {"$in": [pais, "worldwide"]}
            }},
            # 2. Agrupar por hora y país para tener la lista de tendencias
            {
                "$group": {
                    "_id": {
                        "hour": {"$hour": "$scraped_at"},
                        "pais": "$pais"
                    },
                    "trends": {"$addToSet": "$tendencia"}
                }
            },
            # 3. Re-agrupar solo por hora para tener ambos sets de tendencias juntos
            {
                "$group": {
                    "_id": "$_id.hour",
                    "sets": {
                        "$push": {
                            "p": "$_id.pais",
                            "t": "$trends"
                        }
                    }
                }
            },
            # 4. Calcular Intersección y Unión entre Worldwide y el País
            {
                "$project": {
                    "hour": "$_id",
                    "worldwide_set": {
                        "$filter": {"input": "$sets", "as": "s", "cond": {"$eq": ["$$s.p", "worldwide"]}}
                    },
                    "local_set": {
                        "$filter": {"input": "$sets", "as": "s", "cond": {"$eq": ["$$s.p", pais]}}
                    }
                }
            },
            {
                "$project": {
                    "hour": 1,
                    "intersection": {"$size": {"$setIntersection": [
                        {"$arrayElemAt": ["$worldwide_set.t", 0]},
                        {"$arrayElemAt": ["$local_set.t", 0]}
                    ]}},
                    "union": {"$size": {"$setUnion": [
                        {"$arrayElemAt": ["$worldwide_set.t", 0]},
                        {"$arrayElemAt": ["$local_set.t", 0]}
                    ]}}
                }
            },
            # 5. Calcular porcentaje final de sincronía
            {
                "$project": {
                    "hour": 1,
                    "sync_index": {
                        "$cond": [
                            {"$gt": ["$union", 0]},
                            {"$multiply": [{"$divide": ["$intersection", "$union"]}, 100]},
                            0
                        ]
                    }
                }
            },
            {"$sort": {"hour": 1}}
        ]
        return list(cls.collection.aggregate(pipeline))
    
    @classmethod
    def aggregate_survival_stats(cls, pais, dt_from, dt_to, granularity="hour"):
        if granularity == "hour":
            bins = [0, 3, 9, 24]
            labels = ["Fugaz (<3h)", "Activa (3-8h)", "Persistente (9-23h)", "Inmortal (>=24h)"]
        else:
            bins = [0, 1, 3, 7]
            labels = ["Efímera (<1d)", "Estable (1-2d)", "Semanal (3-6d)", "Histórica (>=7d)"]

        pipeline = [
            {"$match": {"scraped_at": {"$gte": dt_from, "$lte": dt_to}, "pais": pais}},
            {
                "$addFields": {
                    "time_unit": {
                        "$dateTrunc": {
                            "date": "$scraped_at",
                            "unit": granularity,
                            "timezone": "-05:00"
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": {"$trim": {"input": "$tendencia"}},
                    "duration": {"$addToSet": "$time_unit"}
                }
            },
            {
                "$project": {
                    "trend_name": "$_id", # Guardamos el nombre
                    "total_units": {"$size": "$duration"}
                }
            },
            # --- PASO CLAVE: Ordenar por duración descendente ---
            {"$sort": {"total_units": -1}}, 
            {
                "$bucket": {
                    "groupBy": "$total_units",
                    "boundaries": bins,
                    "default": "Superior",
                    "output": { 
                        "count": { "$sum": 1 },
                        "trends": { "$push": "$trend_name" } # El $push mantendrá el orden del $sort
                    }
                }
            }
        ]
        
        raw_data = list(cls.collection.aggregate(pipeline))
        
        # Usamos los límites como llaves para mapear fácil
        conteo_final = {b: 0 for b in bins}
        conteo_final["Superior"] = 0

        for item in raw_data:
            conteo_final[item["_id"]] = item["count"]

        # Formatear para el frontend
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
                "topTrends": trends[:3] # Enviamos solo las primeras 3 para el tooltip
            })
        
        return formatted