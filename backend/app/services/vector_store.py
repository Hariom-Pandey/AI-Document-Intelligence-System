import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

try:
    if os.name == "nt":
        import torch  # Preload OpenMP runtime DLL for Windows
except ImportError:
    pass

try:
    import faiss
except Exception as e:
    faiss = None

from app.core.config import settings
from app.services.embeddings import EmbeddingService

logger = logging.getLogger(__name__)

INDEX_FILE = settings.INDEX_DIR / "faiss.index"
META_FILE = settings.INDEX_DIR / "faiss_meta.json"
NPY_FILE = settings.INDEX_DIR / "vectors.npy"

class VectorStore:
    """
    Manages vector index for dense semantic search and RAG retrieval.
    Prefers native FAISS IndexFlatIP; gracefully falls back to pure NumPy
    cosine inner-product search if native C++/SWIG FAISS DLLs fail to load.
    """

    def __init__(self):
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
        self.index: Optional[Any] = None
        self.vectors: Optional[np.ndarray] = None
        self.metadata: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        try:
            if META_FILE.exists():
                with open(str(META_FILE), "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)

            if faiss is not None and INDEX_FILE.exists():
                try:
                    self.index = faiss.read_index(str(INDEX_FILE))
                    logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors.")
                    return
                except Exception as ex:
                    logger.warning(f"Could not read FAISS index file: {ex}. Checking numpy fallback.")

            if NPY_FILE.exists():
                self.vectors = np.load(str(NPY_FILE))
                logger.info(f"Loaded existing NumPy vector store with {len(self.vectors)} vectors.")
            elif faiss is not None:
                self.index = faiss.IndexFlatIP(self.dimension)
                logger.info("Initialized new FAISS IndexFlatIP.")
            else:
                self.vectors = np.empty((0, self.dimension), dtype=np.float32)
                logger.info("Initialized NumPy vector store fallback.")
        except Exception as e:
            logger.error(f"Error loading vector index: {e}. Reinitializing...")
            self.metadata = []
            if faiss is not None:
                try:
                    self.index = faiss.IndexFlatIP(self.dimension)
                except Exception:
                    self.index = None
                    self.vectors = np.empty((0, self.dimension), dtype=np.float32)
            else:
                self.vectors = np.empty((0, self.dimension), dtype=np.float32)

    def _save(self):
        try:
            settings.INDEX_DIR.mkdir(parents=True, exist_ok=True)
            if faiss is not None and self.index is not None:
                try:
                    faiss.write_index(self.index, str(INDEX_FILE))
                except Exception as ex:
                    logger.warning(f"Failed to write FAISS index: {ex}")

            if self.vectors is not None:
                np.save(str(NPY_FILE), self.vectors)

            with open(str(META_FILE), "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist vector index: {e}")

    def add_document_chunks(self, document_id: str, chunks: List[Dict[str, Any]]):
        if not chunks:
            return

        # First remove any prior entries for this document
        self.delete_document(document_id, save=False)

        texts = [c.get("text", "") for c in chunks]
        embeddings = EmbeddingService.embed_texts(texts)

        if embeddings.shape[0] == 0:
            return

        self.dimension = embeddings.shape[1]

        if faiss is not None:
            try:
                if self.index is None:
                    self.index = faiss.IndexFlatIP(self.dimension)
                self.index.add(embeddings)
            except Exception as ex:
                logger.warning(f"FAISS add failed ({ex}); switching to NumPy vector fallback.")
                self.index = None

        if self.index is None:
            if self.vectors is None or self.vectors.shape[0] == 0:
                self.vectors = embeddings
            else:
                self.vectors = np.vstack([self.vectors, embeddings])

        for c in chunks:
            self.metadata.append({
                "document_id": document_id,
                "chunk_index": c.get("chunk_index", 0),
                "page_number": c.get("page_number", 1),
                "text": c.get("text", "")
            })

        self._save()

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        total_items = self.index.ntotal if (faiss and self.index) else (len(self.vectors) if self.vectors is not None else 0)
        if total_items == 0 or not self.metadata:
            return []

        query_vec = EmbeddingService.embed_query(query)
        fetch_k = min(total_items, top_k * 4 if document_id else top_k)

        if faiss is not None and self.index is not None:
            try:
                distances, indices = self.index.search(query_vec, fetch_k)
                raw_scores = distances[0]
                raw_indices = indices[0]
            except Exception:
                raw_scores = []
                raw_indices = []
        else:
            sims = np.dot(self.vectors, query_vec[0])
            sorted_idx = np.argsort(-sims)[:fetch_k]
            raw_scores = sims[sorted_idx]
            raw_indices = sorted_idx

        results = []
        for score, idx in zip(raw_scores, raw_indices):
            if idx < 0 or idx >= len(self.metadata):
                continue
            meta = self.metadata[idx]

            if document_id and meta.get("document_id") != document_id:
                continue

            results.append({
                "document_id": meta.get("document_id"),
                "chunk_index": meta.get("chunk_index"),
                "page_number": meta.get("page_number"),
                "text": meta.get("text"),
                "score": float(score)  # cosine similarity (-1.0 to 1.0)
            })

            if len(results) >= top_k:
                break

        return results

    def delete_document(self, document_id: str, save: bool = True):
        if not self.metadata:
            return

        remaining_indices = [i for i, m in enumerate(self.metadata) if m.get("document_id") != document_id]
        if len(remaining_indices) == len(self.metadata):
            return  # No vectors for this document

        remaining_meta = [self.metadata[i] for i in remaining_indices]

        if not remaining_meta:
            if faiss is not None:
                try:
                    self.index = faiss.IndexFlatIP(self.dimension)
                except Exception:
                    self.index = None
            self.vectors = np.empty((0, self.dimension), dtype=np.float32)
            self.metadata = []
        else:
            texts = [m["text"] for m in remaining_meta]
            embeddings = EmbeddingService.embed_texts(texts)
            if faiss is not None:
                try:
                    self.index = faiss.IndexFlatIP(self.dimension)
                    self.index.add(embeddings)
                except Exception:
                    self.index = None
            if self.index is None:
                self.vectors = embeddings
            self.metadata = remaining_meta

        if save:
            self._save()

# Singleton vector store instance
vector_store = VectorStore()
