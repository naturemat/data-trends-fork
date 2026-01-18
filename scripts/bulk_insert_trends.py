#!/usr/bin/env python3
"""Script to bulk insert trends from CSV into MongoDB."""

import csv
import os
from datetime import datetime
from app.db import db

def parse_tweet_count(value):
    """Parse tweet_count, handling empty strings and floats."""
    if not value or value.strip() == '':
        return None
    try:
        return int(float(value))
    except ValueError:
        return None

def bulk_insert_trends(csv_path):
    """Bulk insert trends from CSV."""
    trends_collection = db.trends

    documents = []
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            fecha_str = row['fecha']
            hora_str = row['hora']
            trend = row['trend']
            tweet_count = parse_tweet_count(row['tweet_count'])
            country = row['country']

            # Parse fecha and hora
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hora = datetime.strptime(hora_str, '%H:%M:%S').time()

            # Combine into scraped_at
            scraped_at = datetime.combine(fecha, hora)

            document = {
                "fecha": fecha_str,
                "hora": hora_str,
                "tendencia": trend,
                "numeroDeTwits": tweet_count,
                "pais": country,
                "scraped_at": scraped_at
            }
            documents.append(document)

    if documents:
        result = trends_collection.insert_many(documents)
        print(f"Inserted {len(result.inserted_ids)} documents.")
    else:
        print("No documents to insert.")

if __name__ == "__main__":
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'tendencias.csv')
    bulk_insert_trends(csv_path)