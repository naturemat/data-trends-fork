"""MongoDB document models."""

from datetime import datetime
from typing import Optional
from app.db import db
from pymongo import DESCENDING


class Trend:
    """Modelo para tendencias de Twitter."""

    collection = db.trends

    @staticmethod
    def create_document(tendencia: str, numeroDeTwits: Optional[int] = None,
                       pais: str = "worldwide") -> dict:
        """Crea un documento de tendencia."""
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
    def insert_one(cls, document: dict):
        """Inserta un documento en la colección."""
        return cls.collection.insert_one(document)

    @classmethod
    def find_all(cls, limit=None):
        cursor = cls.collection.find().sort("scraped_at", -1)
        if limit is not None:
            cursor = cursor.limit(limit)
        return list(cursor)

    @classmethod
    def find_by_country(cls, pais: str, limit: Optional[int] = None):
        """Encuentra tendencias por país."""
        cursor = cls.collection.find({"pais": pais}).sort("scraped_at", -1)
        if limit is not None:
            cursor = cursor.limit(limit)
        return list(cursor)

    @classmethod
    def find_by_date_range(cls, fecha_inicio: str, fecha_fin: str, limit: Optional[int] = None):
        """Encuentra tendencias por rango de fechas."""
        cursor = cls.collection.find({
            "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin}
        }).sort("scraped_at", -1)
        if limit is not None:
            cursor = cursor.limit(limit)
        return list(cursor)
    
    @classmethod
    def find_latest_per_day(cls, pais: str = None):
        """
        Obtiene el registro más reciente de cada día.
        Si se indica un país, filtra por ese país.
        """
        pipeline = []

        # Filtrar por país si se indica
        if pais:
            pipeline.append({"$match": {"pais": pais}})

        # Ordenar por fecha y hora descendente
        pipeline.append({"$sort": {"fecha": 1, "scraped_at": -1}})

        # Agrupar por fecha, tomando el primer registro de cada grupo
        pipeline.append({
            "$group": {
                "_id": "$fecha",
                "tendencia": {"$first": "$tendencia"},
                "numeroDeTwits": {"$first": "$numeroDeTwits"},
                "pais": {"$first": "$pais"},
                "hora": {"$first": "$hora"},
                "scraped_at": {"$first": "$scraped_at"},
                "_id": {"$first": "$_id"}  # Mantener ObjectId
            }
        })

        # Ordenar por fecha descendente (último primero)
        pipeline.append({"$sort": {"_id": -1}})

        return list(cls.collection.aggregate(pipeline))


