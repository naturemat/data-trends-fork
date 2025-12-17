"""CRUD operations for MongoDB (Trend collection)."""

from typing import List, Dict, Any, Optional

from app.models import Trend

# ---------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------
def create_trend(
    tendencia: str,
    numeroDeTwits: Optional[int] = None,
    pais: str = "worldwide",
) -> str:
    """Inserta una tendencia manual en la base de datos."""

    document = Trend.create_document(tendencia, numeroDeTwits, pais)
    result = Trend.insert_one(document)
    return str(result.inserted_id)


# ---------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------
def get_trends(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Obtiene todas las tendencias, opcionalmente con límite."""

    trends = Trend.find_all(limit)
    _stringify_ids(trends)
    return trends


def get_trends_by_country(
    pais: str,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Obtiene tendencias filtradas por país."""

    trends = Trend.find_by_country(pais, limit)
    _stringify_ids(trends)
    return trends


def get_trends_by_date_range(
    fecha_inicio: str,
    fecha_fin: str,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Obtiene tendencias dentro de un rango de fechas."""

    trends = Trend.find_by_date_range(fecha_inicio, fecha_fin, limit)
    _stringify_ids(trends)
    return trends


def get_latest_per_day(pais: Optional[str] = None) -> List[Dict[str, Any]]:
    """Obtiene el último registro por día, opcionalmente filtrado por país."""

    trends = Trend.find_latest_per_day(pais)
    _stringify_ids(trends)
    return trends


# ---------------------------------------------------------------------
# Bulk insert
# ---------------------------------------------------------------------
def save_scraped_trends(trends_data: List[Dict[str, Any]]) -> int:
    """Guarda múltiples tendencias obtenidas por el scraper."""

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

    result = Trend.collection.insert_many(documents)
    return len(result.inserted_ids)


# ---------------------------------------------------------------------
# Utils
# ---------------------------------------------------------------------
def _stringify_ids(trends: List[Dict[str, Any]]) -> None:
    """Convierte ObjectId a string para serialización JSON."""

    for trend in trends:
        if "_id" in trend:
            trend["_id"] = str(trend["_id"])
