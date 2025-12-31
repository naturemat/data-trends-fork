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
    def aggregate_activity(
        cls,
        pais,
        dt_from,
        dt_to,
        granularity="hour"
    ):
        """
        Métrica de actividad temporal:
        - Conteo de tendencias por hora o por día
        - Incluye tendencias con numeroDeTwits = null
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
                        "$dateTrunc": {"date": "$scraped_at", "unit": granularity}
                    },
                    "trends_set": {"$addToSet": "$tendencia"}  # guardamos solo tendencias únicas
                }
            },
            {
                "$project": {
                    "total_trends": {"$size": "$trends_set"}  # contamos cuántas únicas
                }
            },
            {"$sort": {"_id": 1}}
        ]

        result = list(cls.collection.aggregate(pipeline))

        return [
            {
                "timestamp": r["_id"],
                "total_trends": r["total_trends"]
            }
            for r in result
        ]

    @classmethod
    def aggregate_persistence(
        cls,
        dt_from: datetime,
        dt_to: datetime,
        pais: Optional[str] = None,
        granularity: str = "hour",  # hour | day
        limit: int = 20
    ) -> List[Dict]:

        if granularity not in ("hour", "day"):
            raise ValueError("granularity must be 'hour' or 'day'")

        match = {
            "scraped_at": {
                "$gte": dt_from,
                "$lte": dt_to
            }
        }

        if pais:
            match["pais"] = pais

        pipeline = [
            {"$match": match},

            {
                "$addFields": {
                    "time_unit": {
                        "$dateTrunc": {
                            "date": "$scraped_at",
                            "unit": granularity
                        }
                    }
                }
            },

            {
                "$group": {
                    "_id": "$tendencia",
                    "appearances": {"$sum": 1},
                    "time_units": {"$addToSet": "$time_unit"},
                    "countries": {"$addToSet": "$pais"}
                }
            },

            {
                "$project": {
                    "_id": 0,
                    "trend": "$_id",
                    "appearances": 1,
                    "time_units_active": {"$size": "$time_units"},
                    "countries": 1
                }
            },

            {"$sort": {"appearances": -1}},
            {"$limit": limit}
        ]

        return list(cls.collection.aggregate(pipeline))
    
    @classmethod
    def aggregate_intensity(
        cls,
        dt_from: datetime,
        dt_to: datetime,
        pais: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:

        match = {
            "scraped_at": {
                "$gte": dt_from,
                "$lte": dt_to
            },
            "numeroDeTwits": {"$ne": None}
        }

        if pais:
            match["pais"] = pais

        pipeline = [
            {"$match": match},

            {
                "$group": {
                    "_id": "$tendencia",
                    "avg_tweets": {"$avg": "$numeroDeTwits"},
                    "max_tweets": {"$max": "$numeroDeTwits"},
                    "samples": {"$sum": 1},
                    "countries": {"$addToSet": "$pais"}
                }
            },

            {
                "$project": {
                    "_id": 0,
                    "trend": "$_id",
                    "avg_tweets": {"$round": ["$avg_tweets", 0]},
                    "max_tweets": 1,
                    "samples": 1,
                    "countries": 1
                }
            },

            {"$sort": {"avg_tweets": -1}},
            {"$limit": limit}
        ]

        return list(cls.collection.aggregate(pipeline))
    
    @classmethod
    def aggregate_spread(
        cls,
        dt_from: datetime,
        dt_to: datetime,
        pais: str = "worldwide",  # Añadimos el parámetro pais
        limit: int = 50,
    ) -> List[Dict]:
        
        # 1. Filtro base: Siempre por fecha
        match_query = {
            "scraped_at": {
                "$gte": dt_from,
                "$lte": dt_to
            }
        }

        # 2. Si el usuario filtró por un país específico (que no sea global)
        # primero buscamos qué tendencias existen en ese país.
        if pais and pais != "worldwide":
            # Obtenemos la lista de nombres de tendencias en ese país/rango
            tendencias_locales = cls.collection.distinct("tendencia", {
                **match_query,
                "pais": pais
            })
            # Solo procesamos esas tendencias en el pipeline principal
            match_query["tendencia"] = {"$in": tendencias_locales}

        pipeline = [
            {"$match": match_query}, # Ahora el match es inteligente
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
                            "$in_worldwide", "global",
                            {"$cond": [{"$gte": [{"$size": "$countries"}, 2]}, "regional", "local"]}
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
