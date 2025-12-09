#modelos ORM
# app/models.py
from sqlalchemy import Column, Integer, Text, DateTime
from datetime import datetime
from app.db import Base

class Trend(Base):
    __tablename__ = "trends"

    id = Column(Integer, primary_key=True, index=True)
    hashtag = Column(Text, nullable=False)
    rank = Column(Integer, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
