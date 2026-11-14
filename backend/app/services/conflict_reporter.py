import re
import logging
from typing import List, Dict, Any, Optional, Tuple

from app.core.config import settings
from app.services.statement_matcher import StatementMatcher
from app.services.contradiction_detector import ContradictionDetector
from app.services.numerical_consistency import NumericalConsistencyAnalyzer

logger = logging.getLogger(__name__)

class ConflictReporter:
    """
    Orchestrates candidate statement retrieval, NLI contradiction inference,
    numerical consistency checks, conflict classification, and report assembly.
    """

    CONTRACTUAL_KEYWORDS = {
        "jurisdiction", "governing law", "arbitration", "dispute", "termination",
        "liability", "indemnification", "indemnity", "warranty", "confidentiality",
        "intellectual property", "breach", "force majeure", "severability", "clause"
    }

    RESPONSIBILITY_KEYWORDS = {
        "responsible", "responsibility", "obligation", "duty", "deliverable",
        "scope of work", "assigned to", "liable for", "undertake", "perform",
        "contractor shall", "client shall", "vendor shall", "party shall", "manage"
    }

    @classmethod
    def analyze_document_pair(
        cls,
        doc_a: Dict[str, Any],
        doc_b: Dict[str, Any],
        min_similarity: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Directly compares two specific documents and returns a structured consistency report.
        """
        return cls.generate_consistency_report([doc_a, doc_b], min_similarity=min_similarity)

    @classmethod
    def generate_consistency_report(
        cls,
        documents: List[Dict[str, Any]],
        min_similarity: Optional[float] = None,
        job_progress_callback = None
    ) -> Dict[str, Any]:
        """
        Runs the full cross-document consistency detection pipeline over a set of documents.
        """
        if len(documents) < 2:
            return {
                "total_pairs_analyzed": 0,
                "total_conflicts": 0,
                "high_confidence_count": 0,
                "uncertain_count": 0,
                "categories_distribution": {},
                "findings": [],
                "documents": [{"id": d.get("id"), "filename": d.get("filename")} for d in documents]
            }

        # 1. Extract statements for each document
        docs_with_stmts = []
        for doc in documents:
            text = doc.get("extracted_text", "")
            pages = doc.get("pages", [])
            stmts = StatementMatcher.extract_statements(text, pages=pages)
            docs_with_stmts.append({
                "id": doc.get("id"),
                "filename": doc.get("filename", "Document"),
                "statements": stmts
            })

        # 2. Match candidate pairs across distinct document combinations
        candidate_pairs = StatementMatcher.match_collection_candidates(
            docs_with_stmts,
            min_similarity=min_similarity
        )

        total_pairs = len(candidate_pairs)
        conflicts = []
        seen_keys = set()

        # 3. Analyze each candidate pair for numerical, date, or NLI contradictions
        for idx, pair in enumerate(candidate_pairs):
            if job_progress_callback:
                try:
                    job_progress_callback(processed=idx + 1, total=total_pairs)
                except Exception:
                    pass

            stmt_a = pair["statement_a"]
            stmt_b = pair["statement_b"]

            # Prevent duplicate mirror findings
            canon_key = tuple(sorted([stmt_a.strip().lower(), stmt_b.strip().lower()]))
            if canon_key in seen_keys:
                continue

            finding = cls._evaluate_pair(pair)
            if finding:
                seen_keys.add(canon_key)
                conflicts.append(finding)

        # 4. Sort findings by confidence descending
        conflicts.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)

        # 5. Compute summary metrics
        high_conf = sum(1 for c in conflicts if c.get("confidence", 0.0) >= 0.80)
        uncertain = sum(1 for c in conflicts if c.get("review_status") == "needs_review" or c.get("confidence", 0.0) < 0.75)

        cat_dist = {}
        for c in conflicts:
            ctype = c.get("conflict_type", "UNRESOLVED_DIFFERENCE")
            cat_dist[ctype] = cat_dist.get(ctype, 0) + 1

        return {
            "total_pairs_analyzed": total_pairs,
            "total_conflicts": len(conflicts),
            "high_confidence_count": high_conf,
            "uncertain_count": uncertain,
            "categories_distribution": cat_dist,
            "documents": [{"id": d.get("id"), "filename": d.get("filename")} for d in documents],
            "findings": conflicts
        }

    @classmethod
    def _evaluate_pair(cls, pair: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Evaluates a candidate statement pair using both structured numerical analysis
        and deep NLI inference to identify and categorize conflicts.
        """
        stmt_a = pair["statement_a"]
        stmt_b = pair["statement_b"]

        # Step A: Numerical & Date Consistency Check
        num_result = NumericalConsistencyAnalyzer.compare_statements(stmt_a, stmt_b)
        if num_result:
            return {
                "document_a_id": pair["document_a_id"],
                "document_a_name": pair["document_a_name"],
                "document_b_id": pair["document_b_id"],
                "document_b_name": pair["document_b_name"],
                "statement_a": stmt_a,
                "statement_b": stmt_b,
                "page_a": pair["page_a"],
                "page_b": pair["page_b"],
                "conflict_type": num_result["conflict_type"],
                "nli_label": "CONTRADICTION",
                "confidence": num_result["confidence"],
                "explanation": num_result["explanation"],
                "evidence_context": num_result.get("evidence_context", {}),
                "review_status": num_result.get("review_status", "needs_review")
            }

        # Step B: Natural Language Inference (NLI) Contradiction Check
        nli_res = ContradictionDetector.classify_pair(stmt_a, stmt_b)

        if nli_res.get("label") == "CONTRADICTION":
            confidence = nli_res.get("confidence", 0.70)
            threshold = getattr(settings, "CONTRADICTION_CONFIDENCE_THRESHOLD", 0.60)

            if confidence >= threshold:
                c_type = cls._categorize_nli_conflict(stmt_a, stmt_b)
                explanation = cls._generate_explanation(stmt_a, stmt_b, c_type, nli_res)

                return {
                    "document_a_id": pair["document_a_id"],
                    "document_a_name": pair["document_a_name"],
                    "document_b_id": pair["document_b_id"],
                    "document_b_name": pair["document_b_name"],
                    "statement_a": stmt_a,
                    "statement_b": stmt_b,
                    "page_a": pair["page_a"],
                    "page_b": pair["page_b"],
                    "conflict_type": c_type,
                    "nli_label": "CONTRADICTION",
                    "confidence": confidence,
                    "explanation": explanation,
                    "evidence_context": {
                        "detection_method": nli_res.get("detection_method"),
                        "fallback_active": nli_res.get("fallback_active", False),
                        "rationale": nli_res.get("rationale", "NLI classified as direct proposition contradiction"),
                        "semantic_similarity": pair.get("similarity", 0.0)
                    },
                    "review_status": "needs_review" if confidence < 0.80 else "confirmed_conflict"
                }

        # Step C: Entity Inconsistency Check (e.g. "Vendor is ABC Inc." vs "Vendor is XYZ Corp.")
        entity_conflict = cls._check_entity_inconsistency(stmt_a, stmt_b)
        if entity_conflict:
            return {
                "document_a_id": pair["document_a_id"],
                "document_a_name": pair["document_a_name"],
                "document_b_id": pair["document_b_id"],
                "document_b_name": pair["document_b_name"],
                "statement_a": stmt_a,
                "statement_b": stmt_b,
                "page_a": pair["page_a"],
                "page_b": pair["page_b"],
                "conflict_type": "ENTITY_INCONSISTENCY",
                "nli_label": "CONTRADICTION",
                "confidence": 0.82,
                "explanation": entity_conflict["explanation"],
                "evidence_context": entity_conflict,
                "review_status": "needs_review"
            }

        return None

    @classmethod
    def _categorize_nli_conflict(cls, stmt_a: str, stmt_b: str) -> str:
        """
        Determines the specific domain category of the contradiction.
        """
        combined = (stmt_a + " " + stmt_b).lower()

        # Contractual check
        if any(kw in combined for kw in cls.CONTRACTUAL_KEYWORDS):
            return "CONTRACTUAL_CONFLICT"

        # Responsibility check
        if any(kw in combined for kw in cls.RESPONSIBILITY_KEYWORDS):
            return "RESPONSIBILITY_CONFLICT"

        # Version change / revision marker check
        rev_markers = {"revised", "amended", "updated", "superseded", "replaces", "version", "new"}
        words = set(re.findall(r"\b[a-zA-Z]+\b", combined))
        if any(rm in words for rm in rev_markers):
            return "POTENTIAL_VERSION_CHANGE"

        # Default to factual contradiction
        return "FACTUAL_CONTRADICTION"

    @classmethod
    def _generate_explanation(
        cls,
        stmt_a: str,
        stmt_b: str,
        conflict_type: str,
        nli_res: Dict[str, Any]
    ) -> str:
        """
        Produces an explainable rationale for why this pair was flagged as contradictory.
        """
        category_human = conflict_type.replace("_", " ").title()
        method_note = " (Detected via local NLI neural model)" if not nli_res.get("fallback_active") else " (Detected via semantic opposition rules)"

        if conflict_type == "CONTRACTUAL_CONFLICT":
            return (
                f"{category_human}: The documents assert mutually incompatible contractual terms, "
                f"obligations, or legal clauses{method_note}."
            )
        elif conflict_type == "RESPONSIBILITY_CONFLICT":
            return (
                f"{category_human}: Conflicting assignment of duties, party obligations, "
                f"or scope of work between Document A and Document B{method_note}."
            )
        elif conflict_type == "POTENTIAL_VERSION_CHANGE":
            return (
                f"{category_human}: Document statements indicate an updated, superseded, "
                f"or amended provision that differs from an earlier assertion."
            )
        else:
            rationale = nli_res.get("rationale", "")
            details = f" Reason: {rationale}" if rationale else ""
            return f"Factual Contradiction: Statements make conflicting assertions that cannot be simultaneously valid.{details}"

    @classmethod
    def _check_entity_inconsistency(cls, stmt_a: str, stmt_b: str) -> Optional[Dict[str, Any]]:
        """
        Checks if both statements define the same entity role (e.g., 'primary contractor', 'client', 'CEO')
        with different named entities.
        """
        role_patterns = [
            r"\b(client|customer)\s+is\s+([A-Z][a-zA-Z0-9\s,\.]+)",
            r"\b(vendor|contractor|supplier)\s+is\s+([A-Z][a-zA-Z0-9\s,\.]+)",
            r"\b(project\s+manager|lead|director)\s+is\s+([A-Z][a-zA-Z\s]+)",
            r"\b(governing\s+law)\s+(?:is|shall\s+be)\s+(?:the\s+)?([A-Za-z\s]+)",
            r"\b(jurisdiction)\s+(?:is|shall\s+be)\s+(?:the\s+)?([A-Za-z\s]+)"
        ]

        for pat in role_patterns:
            m_a = re.search(pat, stmt_a, re.IGNORECASE)
            m_b = re.search(pat, stmt_b, re.IGNORECASE)

            if m_a and m_b:
                role_a = m_a.group(1).lower().strip()
                role_b = m_b.group(1).lower().strip()
                val_a = m_a.group(2).strip().rstrip(".")
                val_b = m_b.group(2).strip().rstrip(".")

                if role_a == role_b and val_a.lower() != val_b.lower():
                    return {
                        "role": role_a,
                        "value_a": val_a,
                        "value_b": val_b,
                        "explanation": (
                            f"Entity discrepancy for '{role_a.title()}': "
                            f"Document A identifies '{val_a}', while Document B identifies '{val_b}'."
                        )
                    }

        return None
