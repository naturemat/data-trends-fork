from app.db import db
from datetime import datetime, timezone

class Trend:
    # Referencia a la colección en MongoDB
    collection = db.trends

    @classmethod
    def create(cls, data):
        """Crea un nuevo documento."""
        return cls.collection.insert_one(data)

    @classmethod
    def find_all(cls, query={}, limit=0):
        """Busca documentos básicos."""
        cursor = cls.collection.find(query).sort("scraped_at", -1)
        if limit > 0:
            cursor = cursor.limit(limit)
        return list(cursor)

    # --- AQUÍ ESTÁN LAS FUNCIONES QUE FALTABAN (LAS QUE DABAN ERROR 500) ---

    @classmethod
    def aggregate_activity(cls, pais, dt_from, dt_to, granularity="hour"):
        """Calcula el volumen de tendencias por hora/día."""
        match_stage = {
            "scraped_at": {"$gte": dt_from, "$lte": dt_to}
        }
        if pais and pais != "worldwide" and pais != "all":
            match_stage["pais"] = pais

        # Formato de fecha para agrupar (Mongo syntax)
        date_format = "%Y-%m-%d-%H" if granularity == "hour" else "%Y-%m-%d"

        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {"format": date_format, "date": "$scraped_at"}
                    },
                    "total_trends": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}},
            {
                "$project": {
                    "_id": 0,
                    "timestamp": "$_id",
                    "total_trends": 1
                }
            }
        ]
        return list(cls.collection.aggregate(pipeline))

    @classmethod
    def aggregate_intensity(cls, dt_from, dt_to, pais, limit=20):
        """Calcula Max vs Promedio de tweets por tendencia."""
        match_stage = {
            "scraped_at": {"$gte": dt_from, "$lte": dt_to}
        }
        if pais and pais != "worldwide" and pais != "all":
            match_stage["pais"] = pais

        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": "$tendencia",
                    "max_tweets": {"$max": "$numeroDeTwits"},
                    "avg_tweets": {"$avg": "$numeroDeTwits"},
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"max_tweets": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "trend": "$_id",
                    "max_tweets": 1,
                    "avg_tweets": {"$round": ["$avg_tweets", 0]}
                }
            }
        ]
        return list(cls.collection.aggregate(pipeline))

    @classmethod
    def aggregate_persistence(cls, dt_from, dt_to, pais, granularity, limit=20):
        """Cuenta cuántas veces apareció una tendencia (frecuencia)."""
        match_stage = {
            "scraped_at": {"$gte": dt_from, "$lte": dt_to}
        }
        if pais and pais != "worldwide" and pais != "all":
            match_stage["pais"] = pais

        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": "$tendencia",
                    "appearances": {"$sum": 1},
                    "last_seen": {"$max": "$scraped_at"}
                }
            },
            {"$sort": {"appearances": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "trend": "$_id",
                    "appearances": 1
                }
            }
        ]
        return list(cls.collection.aggregate(pipeline))

    @classmethod
    def aggregate_spread(cls, dt_from, dt_to, pais, limit=50):
        """Analiza en cuántos países aparece cada tendencia."""
        match_stage = {
            "scraped_at": {"$gte": dt_from, "$lte": dt_to}
        }
        
        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": "$tendencia",
                    "countries": {"$addToSet": "$pais"},
                    "tweet_volume": {"$max": "$numeroDeTwits"}
                }
            },
            {
                "$project": {
                    "trend": "$_id",
                    "countries": 1,
                    "countries_count": {"$size": "$countries"},
                    "tweet_volume": 1,
                    "_id": 0
                }
            },
            {"$sort": {"countries_count": -1, "tweet_volume": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "trend": 1,
                    "countries": 1,
                    "scope": {
                        "$cond": {
                            "if": {"$gt": ["$countries_count", 1]},
                            "then": "global",
                            "else": "local"
                        }
                    },
                    "in_worldwide": {"$in": ["worldwide", "$countries"]}
                }
            }
        ]
        return list(cls.collection.aggregate(pipeline))