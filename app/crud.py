"""CRUD operations for MongoDB."""

from typing import List, Dict, Any, Optional
from app.models import Trend


def create_trend(tendencia: str, numeroDeTwits: Optional[int] = None,
                pais: str = "worldwide") -> str:
    """Crea una nueva tendencia en la base de datos."""
    document = Trend.create_document(tendencia, numeroDeTwits, pais)
    result = Trend.insert_one(document)
    return str(result.inserted_id)


def get_trends(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    trends = Trend.find_all(limit)
    for trend in trends:
        trend["_id"] = str(trend["_id"])
    return trends

def get_trends_by_country(pais: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    trends = Trend.find_by_country(pais, limit)
    for trend in trends:
        trend["_id"] = str(trend["_id"])
    return trends

def get_trends_by_date_range(fecha_inicio: str, fecha_fin: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    trends = Trend.find_by_date_range(fecha_inicio, fecha_fin, limit)
    for trend in trends:
        trend["_id"] = str(trend["_id"])
    return trends


def save_scraped_trends(trends_data: List[Dict[str, Any]]) -> int:
    """Guarda múltiples tendencias del scraper."""
    documents = []
    for trend in trends_data:
        document = Trend.create_document(
            tendencia=trend["trend"],
            numeroDeTwits=trend.get("tweet_count"),
            pais=trend.get("country", "worldwide")
        )
        documents.append(document)

    if documents:
        result = Trend.collection.insert_many(documents)
        return len(result.inserted_ids)
    return 0

def get_latest_per_day(pais: str = None):
    """Obtiene el último registro de cada día, opcionalmente filtrando por país."""
    trends = Trend.find_latest_per_day(pais)
    for trend in trends:
        trend["_id"] = str(trend["_id"])  # Convertir ObjectId a string
    return trends
