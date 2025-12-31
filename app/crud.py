"""CRUD operations for MongoDB (Trend collection)."""

from typing import List, Dict, Any, Optional
from app.models import Trend

# ---------------------------------------------------------------------
# Create (Individual)
# ---------------------------------------------------------------------
def create_trend(
    tendencia: str,
    numeroDeTwits: Optional[int] = None,
    pais: str = "worldwide",
) -> str:
    """Inserta una tendencia manual en la base de datos."""
    # Usamos el método estático que ya tienes en models.py
    document = Trend.create_document(tendencia, numeroDeTwits, pais)
    result = Trend.insert_one(document)
    return str(result.inserted_id)


# ---------------------------------------------------------------------
# Bulk insert (EL QUE USA EL SCRAPER)
# ---------------------------------------------------------------------
def save_scraped_trends(trends_data: List[Dict[str, Any]]) -> int:
    """Guarda múltiples tendencias obtenidas por el scraper."""

    # Generamos los documentos usando tu método estático de models.py
    documents = [
        Trend.create_document(
            tendencia=trend.get("trend"),
            numeroDeTwits=trend.get("tweet_count"),
            pais=trend.get("country", "worldwide"),
        )
        for trend in trends_data
        if trend.get("trend")
    ]

    if not documents:
        return 0

    # Usamos la colección directamente desde la clase Trend
    result = Trend.collection.insert_many(documents)
    return len(result.inserted_ids)


# ---------------------------------------------------------------------
# Read y Utils
# ---------------------------------------------------------------------
def get_trends(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    trends = Trend.find_all(limit)
    _stringify_ids(trends)
    return trends

def get_trends_by_country(pais: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    trends = Trend.find_by_country(pais, limit)
    _stringify_ids(trends)
    return trends

def get_trends_by_date_range(fecha_inicio: str, fecha_fin: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    trends = Trend.find_by_date_range(fecha_inicio, fecha_fin, limit)
    _stringify_ids(trends)
    return trends

def _stringify_ids(trends: List[Dict[str, Any]]) -> None:
    for trend in trends:
        if "_id" in trend:
            trend["_id"] = str(trend["_id"])