import logging
import os
import numpy as np
from typing import List, Union

from app.core.config import settings

logger = logging.getLogger(__name__)

_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer model: {settings.EMBEDDING_MODEL_NAME}...")
            try:
                _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME, local_files_only=True)
            except Exception:
                logger.info("Local cache not found. Downloading model from Hugging Face...")
                _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.error(f"Could not initialize SentenceTransformer ({e}). Using feature hash fallback.")
            _embedding_model = "hash_fallback"
    return _embedding_model

class EmbeddingService:
    """
    Computes dense vector representations for document passages and search queries.
    """

    @staticmethod
    def get_dimension() -> int:
        model = get_embedding_model()
        if hasattr(model, "get_sentence_embedding_dimension"):
            return model.get_sentence_embedding_dimension()
        return 384

    @staticmethod
    def embed_texts(texts: List[str]) -> np.ndarray:
        if not texts:
            dim = EmbeddingService.get_dimension()
            return np.empty((0, dim), dtype=np.float32)

        model = get_embedding_model()
        if model != "hash_fallback" and hasattr(model, "encode"):
            try:
                embeddings = model.encode(
                    texts,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                    normalize_embeddings=True
                )
                return embeddings.astype(np.float32)
            except Exception as ex:
                logger.warning(f"SentenceTransformer encoding failed ({ex}), using feature hash.")

        # Robust, high-speed feature-hash fallback (zero memory, instant)
        import hashlib
        dim = 384
        res = []
        for t in texts:
            vec = np.zeros(dim, dtype=np.float32)
            for w in t.lower().split():
                h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16) % dim
                vec[h] += 1.0
            norm = float(np.linalg.norm(vec))
            if norm > 0:
                vec = vec / norm
            res.append(vec)
        return np.array(res, dtype=np.float32)

    @staticmethod
    def embed_query(query: str) -> np.ndarray:
        return EmbeddingService.embed_texts([query])

