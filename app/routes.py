"""Flask route handlers for trends API."""

from flask import Blueprint, request, jsonify
from app.db import get_session
from app.crud import create_trend, get_trends

routes_blueprint = Blueprint("routes", __name__)


@routes_blueprint.get("/trends")
def list_trends():
    db = get_session()
    try:
        trends = get_trends(db)
        return jsonify([
            {"id": t.id, "hashtag": t.hashtag, "rank": t.rank, "scraped_at": t.scraped_at.isoformat()}
            for t in trends
        ])
    finally:
        db.close()


@routes_blueprint.post("/trends")
def add_trend():
    db = get_session()
    try:
        data = request.json
        trend = create_trend(db, data["hashtag"], data.get("rank"))
        return jsonify({"message": "Trend creado", "id": trend.id})
    finally:
        db.close()
