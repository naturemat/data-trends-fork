"""CRUD operations for MongoDB (Trend collection)."""

from typing import Any, Dict, List

from app.models import Trend


# ---------------------------------------------------------------------
# Bulk insert (el que usa el scraper)
# ---------------------------------------------------------------------
def save_scraped_trends(trends_data: List[Dict[str, Any]]) -> int:
    """Guarda en MongoDB las tendencias obtenidas por el scraper."""
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
