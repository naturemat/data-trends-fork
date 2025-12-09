# endpoints manejadas por Flaskfrom flask import Blueprint, request, jsonify
from flask import Blueprint, jsonify
from requests import request
from app.db import get_db
from app.crud import create_trend, get_trends

routes_blueprint = Blueprint("routes", __name__)

@routes_blueprint.get("/trends")
def list_trends():
    db = next(get_db())
    trends = get_trends(db)
    return jsonify([
        {"id": t.id, "hashtag": t.hashtag, "rank": t.rank, "scraped_at": t.scraped_at.isoformat()}
        for t in trends
    ])

@routes_blueprint.post("/trends")
def add_trend():
    db = next(get_db())
    data = request.json
    trend = create_trend(db, data["hashtag"], data.get("rank"))
    return jsonify({"message": "Trend creado", "id": trend.id})
