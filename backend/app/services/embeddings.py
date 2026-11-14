import logging
import os
import numpy as np
from typing import List, Union

# Enforce local/offline execution for zero-latency local inference
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from sentence_transformers import SentenceTransformer
from app.core.config import settings

logger = logging.getLogger(__name__)

_embedding_model = None

def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading SentenceTransformer model: {settings.EMBEDDING_MODEL_NAME}...")
        try:
            _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME, local_files_only=True)
        except Exception:
            _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        logger.info("SentenceTransformer model loaded successfully.")
    return _embedding_model

class EmbeddingService:
    """
    Computes dense vector representations for document passages and search queries.
    """

    @staticmethod
    def get_dimension() -> int:
        model = get_embedding_model()
        return model.get_sentence_embedding_dimension()

    @staticmethod
    def embed_texts(texts: List[str]) -> np.ndarray:
        if not texts:
            dim = EmbeddingService.get_dimension()
            return np.empty((0, dim), dtype=np.float32)

        model = get_embedding_model()
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True
        )
        return embeddings.astype(np.float32)

    @staticmethod
    def embed_query(query: str) -> np.ndarray:
        model = get_embedding_model()
        embedding = model.encode(
            [query],
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True
        )
        return embedding.astype(np.float32)

