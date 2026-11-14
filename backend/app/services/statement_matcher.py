import re
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from app.core.config import settings
from app.services.embeddings import EmbeddingService
from app.services.ner import EntityExtractor, get_spacy_nlp

logger = logging.getLogger(__name__)

class StatementMatcher:
    """
    Identifies meaningful declarative statements across documents and performs
    semantic candidate retrieval to produce relevant statement pairs for contradiction analysis.
    """

    @classmethod
    def extract_statements(cls, text: str, pages: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Splits document text or page objects into discrete, meaningful statements
        while preserving physical page associations.
        """
        statements = []

        # If structured pages are provided, extract page-by-page
        if pages and len(pages) > 0:
            for p in pages:
                p_num = p.get("page_number", 1)
                p_text = p.get("text", "")
                page_stmts = cls._split_into_sentences(p_text)
                for s in page_stmts:
                    if cls._is_meaningful_statement(s):
                        statements.append({
                            "text": s.strip(),
                            "page_number": p_num
                        })
        else:
            # Fallback to full text sentence splitting with page 1 default
            sentences = cls._split_into_sentences(text)
            for s in sentences:
                if cls._is_meaningful_statement(s):
                    statements.append({
                        "text": s.strip(),
                        "page_number": 1
                    })

        return statements

    @classmethod
    def find_candidate_pairs(
        cls,
        doc_a_data: Dict[str, Any],
        doc_b_data: Dict[str, Any],
        min_similarity: Optional[float] = None,
        max_pairs: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retrieves semantically and conceptually related statement pairs between Document A and Document B.
        Uses Sentence Transformers embeddings and entity overlap to prune unrelated statements.
        """
        sim_threshold = min_similarity if min_similarity is not None else settings.CONSISTENCY_SIMILARITY_THRESHOLD

        stmts_a = doc_a_data.get("statements", [])
        stmts_b = doc_b_data.get("statements", [])

        if not stmts_a or not stmts_b:
            return []

        texts_a = [s["text"] for s in stmts_a]
        texts_b = [s["text"] for s in stmts_b]

        # 1. Compute dense embeddings for both sets of statements
        emb_a = EmbeddingService.embed_texts(texts_a)
        emb_b = EmbeddingService.embed_texts(texts_b)

        if emb_a.shape[0] == 0 or emb_b.shape[0] == 0:
            return []

        # 2. Compute pairwise cosine similarity matrix: Shape (len(A), len(B))
        # Note: embeddings from EmbeddingService are normalized (norm = 1.0)
        sim_matrix = np.dot(emb_a, emb_b.T)

        candidate_pairs = []
        seen_pairs = set()

        # 3. Filter pairs above similarity threshold or with shared key entity contexts
        for i in range(len(texts_a)):
            for j in range(len(texts_b)):
                sim = float(sim_matrix[i, j])
                
                # Check entity or numerical context overlap to rescue low-cosine yet conflicting numbers
                has_entity_anchor = cls._has_entity_anchor(texts_a[i], texts_b[j])

                # Condition: High semantic similarity OR moderate similarity with shared entity anchor
                if sim >= sim_threshold or (sim >= 0.35 and has_entity_anchor):
                    pair_key = (texts_a[i].lower(), texts_b[j].lower())
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    candidate_pairs.append({
                        "document_a_id": doc_a_data["id"],
                        "document_a_name": doc_a_data.get("filename", "Document A"),
                        "statement_a": texts_a[i],
                        "page_a": stmts_a[i]["page_number"],
                        "document_b_id": doc_b_data["id"],
                        "document_b_name": doc_b_data.get("filename", "Document B"),
                        "statement_b": texts_b[j],
                        "page_b": stmts_b[j]["page_number"],
                        "similarity": round(sim, 4),
                        "has_entity_anchor": has_entity_anchor
                    })

        # Sort candidate pairs by relevance (similarity descending)
        candidate_pairs.sort(key=lambda x: x["similarity"], reverse=True)
        return candidate_pairs[:max_pairs]

    @classmethod
    def match_collection_candidates(
        cls,
        documents_data: List[Dict[str, Any]],
        min_similarity: Optional[float] = None,
        max_pairs_per_doc_pair: int = 40
    ) -> List[Dict[str, Any]]:
        """
        Generates candidate statement pairs across multiple documents in a collection.
        Compares all distinct pairs (doc_i, doc_j) where i < j.
        """
        all_candidate_pairs = []

        n = len(documents_data)
        for i in range(n):
            for j in range(i + 1, n):
                pairs = cls.find_candidate_pairs(
                    documents_data[i],
                    documents_data[j],
                    min_similarity=min_similarity,
                    max_pairs=max_pairs_per_doc_pair
                )
                all_candidate_pairs.extend(pairs)

        return all_candidate_pairs

    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        """
        Splits text into clean sentences using regex and punctuation boundaries.
        """
        if not text:
            return []

        # Normalize line breaks and tabs
        normalized = re.sub(r"[\r\n]+", " ", text)
        normalized = re.sub(r"\s+", " ", normalized).strip()

        # Match sentence boundaries (avoiding common abbreviations like Dr., Mr., vs., etc.)
        pattern = r"(?<=[.!?])\s+(?=[A-Z0-9\"'₹$])"
        raw_splits = re.split(pattern, normalized)

        # Further split on bullet points or semi-colons if length is substantial
        final_sentences = []
        for s in raw_splits:
            s_clean = s.strip()
            # If paragraph contains bullet markers, split them
            if "\u2022" in s_clean or " - " in s_clean:
                bullet_parts = re.split(r"[\u2022]|\s+-\s+", s_clean)
                for bp in bullet_parts:
                    bp_clean = bp.strip()
                    if bp_clean:
                        final_sentences.append(bp_clean)
            else:
                if s_clean:
                    final_sentences.append(s_clean)

        return final_sentences

    @staticmethod
    def _is_meaningful_statement(sentence: str) -> bool:
        """
        Validates if a sentence contains substantive propositional content
        (rejects short headers, page numbers, isolated dates, footer boilerplate).
        """
        s = sentence.strip()
        words = s.split()

        # Must have at least 4 words and fewer than 100 words
        if len(words) < 4 or len(words) > 100:
            return False

        # Must contain at least some alphabetic words
        alpha_count = sum(1 for w in words if any(c.isalpha() for c in w))
        if alpha_count < 3:
            return False

        # Reject pure table headers or page labels
        lower_s = s.lower()
        if re.match(r"^(page\s+\d+|table\s+\d+|figure\s+\d+|chapter\s+\d+|section\s+\d+)", lower_s):
            return False

        return True

    @staticmethod
    def _has_entity_anchor(text_a: str, text_b: str) -> bool:
        """
        Checks if two statements share key anchored topics like money, dates,
        percentages, or subject nouns (e.g., 'budget', 'deadline', 'fee', 'payment').
        """
        anchors = {
            "budget", "cost", "price", "fee", "amount", "total", "payment",
            "deadline", "completion", "timeline", "duration", "date", "schedule",
            "warranty", "penalty", "damages", "interest", "salary", "stipend",
            "liability", "termination", "jurisdiction", "milestone", "delivery"
        }

        tokens_a = set(re.findall(r"\b[a-zA-Z]{3,}\b", text_a.lower()))
        tokens_b = set(re.findall(r"\b[a-zA-Z]{3,}\b", text_b.lower()))

        shared = tokens_a.intersection(tokens_b)
        if any(anchor in shared for anchor in anchors):
            return True

        # Check for currency symbols or percentages in both
        has_currency_a = bool(re.search(r"[₹$€£]|rs\.?|inr|usd", text_a, re.I))
        has_currency_b = bool(re.search(r"[₹$€£]|rs\.?|inr|usd", text_b, re.I))
        if has_currency_a and has_currency_b and len(shared) >= 2:
            return True

        return False

