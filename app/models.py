"""MongoDB document models."""

from datetime import datetime
from typing import Optional
from app.db import db


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
    def find_all(cls, limit: int = 100):
        """Encuentra todos los documentos ordenados por fecha descendente."""
        return list(cls.collection.find().sort("scraped_at", -1).limit(limit))

    @classmethod
    def find_by_country(cls, pais: str, limit: int = 50):
        """Encuentra tendencias por país."""
        return list(cls.collection.find({"pais": pais}).sort("scraped_at", -1).limit(limit))

    @classmethod
    def find_by_date_range(cls, fecha_inicio: str, fecha_fin: str, limit: int = 100):
        """Encuentra tendencias por rango de fechas."""
        return list(cls.collection.find({
            "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin}
        }).sort("scraped_at", -1).limit(limit))
