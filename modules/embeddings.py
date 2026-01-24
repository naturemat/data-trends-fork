"""
Module for handling embeddings and topic enrichment using Hugging Face models and FAISS.
"""

import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from transformers import pipeline
from typing import List, Dict, Tuple, Optional
import pickle


class EmbeddingManager:
    """Manages embeddings generation, topic classification, and FAISS index for trends."""

    def __init__(self, embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 topic_model_name: str = "cardiffnlp/tweet-topic-21-multi",
                 index_path: str = "faiss_index.idx",
                 metadata_path: str = "faiss_metadata.pkl"):
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.topic_classifier = pipeline("text-classification", model=topic_model_name, tokenizer=topic_model_name)
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.index = None
        self.metadata: List[Dict] = []  # List of dicts: {"trend_id": str, "trend_text": str, "topic": str}
        self.load_index()

    def load_index(self):
        """Load FAISS index and metadata from disk if they exist."""
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
        else:
            # Initialize empty index (dimension based on model)
            dim = self.embedding_model.get_sentence_embedding_dimension()
            self.index = faiss.IndexFlatIP(dim)  # Inner product for cosine similarity

    def save_index(self):
        """Save FAISS index and metadata to disk."""
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding vector for a given text."""
        return self.embedding_model.encode(text, convert_to_numpy=True)

    def classify_topic(self, text: str) -> str:
        """Classify the topic of a given text using the topic model."""
        result = self.topic_classifier(text)
        return result[0]['label'] if result else 'unknown'

    def add_trend(self, trend_id: str, trend_text: str):
        """Add a trend's embedding and metadata to the index."""
        embedding = self.generate_embedding(trend_text)
        topic = self.classify_topic(trend_text)

        # Normalize for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)

        # Add to FAISS index
        self.index.add(np.array([embedding], dtype=np.float32))

        # Add metadata
        self.metadata.append({
            "trend_id": trend_id,
            "trend_text": trend_text,
            "topic": topic
        })

        # Save after adding
        self.save_index()

    def search_similar(self, query_text: str, top_k: int = 10) -> List[Dict]:
        """Search for similar trends based on query text."""
        if self.index.ntotal == 0:
            return []  # No data to search

        query_embedding = self.generate_embedding(query_text)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        query_embedding = np.array([query_embedding], dtype=np.float32)

        # Search FAISS
        distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):
                meta = self.metadata[idx]
                results.append({
                    "trend_id": meta["trend_id"],
                    "trend_text": meta["trend_text"],
                    "topic": meta["topic"],
                    "similarity": float(dist)
                })

        return results

    def get_all_enriched_trends(self) -> List[Dict]:
        """Return all trends with their topics."""
        return self.metadata


# Global instance
embedding_manager = EmbeddingManager()