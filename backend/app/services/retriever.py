import re
import logging
from typing import List, Dict, Any, Optional
from app.services.vector_store import vector_store
from app.core.config import settings

logger = logging.getLogger(__name__)

class DocumentRetriever:
    """
    Hybrid Retriever combining dense Sentence-Transformer vector search with
    lexical keyword scoring and Reciprocal Rank Fusion for maximum retrieval accuracy.
    """

    @classmethod
    def retrieve(
        cls,
        query: str,
        document_id: Optional[str] = None,
        top_k: Optional[int] = None,
        min_score: float = 0.20
    ) -> List[Dict[str, Any]]:
        k = top_k or settings.TOP_K_CHUNKS

        # 1. Fetch dense candidates from FAISS (fetch wider candidate pool)
        dense_results = vector_store.search(
            query=query,
            top_k=max(k * 2, 8),
            document_id=document_id
        )

        if not dense_results:
            return []

        # 2. Compute Hybrid Lexical Re-ranking
        ranked_chunks = cls._hybrid_rerank(query, dense_results)

        # 3. Filter by relevance threshold
        filtered = [r for r in ranked_chunks if r.get("score", 0.0) >= min_score]
        
        # If strict threshold filtered everything out, return top result if above baseline
        if not filtered and ranked_chunks and ranked_chunks[0].get("score", 0.0) >= 0.15:
            filtered = [ranked_chunks[0]]

        return filtered[:k]

    @staticmethod
    def _hybrid_rerank(query: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Combines dense vector similarity with sparse lexical keyword matching.
        Particularly boosts exact numbers, codes, dates, and proper names.
        """
        # Extract query terms, filter short words
        tokens = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]
        stopwords = {"what", "when", "where", "which", "who", "whom", "this", "that", "from", "with", "have", "does", "about"}
        keywords = [t for t in tokens if t not in stopwords]

        reranked = []
        for chunk in chunks:
            text_lower = chunk.get("text", "").lower()
            dense_score = float(chunk.get("score", 0.0))

            # Compute lexical matching bonus
            lexical_score = 0.0
            if keywords:
                matches = sum(1 for kw in keywords if kw in text_lower)
                lexical_score = matches / len(keywords)

                # Special boost if exact query phrase or alphanumeric patterns appear
                if query.lower() in text_lower:
                    lexical_score += 0.3

            # Hybrid score: 70% dense semantic + 30% lexical keyword overlap
            hybrid_score = round(0.70 * dense_score + 0.30 * min(lexical_score, 1.0), 4)

            item = dict(chunk)
            item["score"] = hybrid_score
            item["dense_score"] = round(dense_score, 4)
            item["lexical_score"] = round(lexical_score, 4)
            reranked.append(item)

        # Sort by final hybrid score descending
        reranked.sort(key=lambda x: x["score"], reverse=True)
        return reranked

    @staticmethod
    def build_context(chunks: List[Dict[str, Any]]) -> str:
        """
        Formats retrieved chunks into a grounded context string with page tags.
        """
        if not chunks:
            return ""

        context_parts = []
        for i, chunk in enumerate(chunks):
            page = chunk.get("page_number", 1)
            text = chunk.get("text", "").strip()
            context_parts.append(f"[Source {i+1} - Page {page}]:\n{text}")

        return "\n\n".join(context_parts)
