"""
Script para enriquecer la data de trends en MongoDB con embeddings y categorias o topic´s.
Se ejecuta una vez para llenar el FAISS con datos existentes.
"""

import sys
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

print(f"Loaded .env from {env_path}")
print(f"MONGODB_URL: {os.getenv('MONGODB_URL')}")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.models import Trend
from modules.embeddings import embedding_manager

def enrich_existing_trends():
    """Load all trends from MongoDB and add to FAISS."""
    trends = Trend.find_all(limit=None)  # Get all trends

    for trend in trends:
        trend_id = str(trend["_id"])
        trend_text = trend["tendencia"]
        # Add to FAISS (includes topic classification)
        embedding_manager.add_trend(trend_id, trend_text)
        print(f"Enriched: {trend_text}")

    print(f"Enriched {len(trends)} trends.")

if __name__ == "__main__":
    enrich_existing_trends()