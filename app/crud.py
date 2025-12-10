"""CRUD helpers for the API and scraper."""

from sqlalchemy.orm import Session
from app.models import Trend


def create_trend(db: Session, hashtag: str, rank: int | None = None):
    new_trend = Trend(hashtag=hashtag, rank=rank)
    db.add(new_trend)
    db.commit()
    db.refresh(new_trend)
    return new_trend


def get_trends(db: Session):
    return db.query(Trend).order_by(Trend.rank.asc()).all()
