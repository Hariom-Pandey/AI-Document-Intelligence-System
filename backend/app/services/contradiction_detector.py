import re
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from app.core.config import settings
from app.services.embeddings import EmbeddingService
from app.services.ner import get_spacy_nlp

logger = logging.getLogger(__name__)

_nli_cross_encoder = None
_model_load_attempted = False

def get_nli_model():
    """
    Singleton loader for the cross-encoder NLI model.
    Loads once and reuses across inference requests.
    """
    global _nli_cross_encoder, _model_load_attempted
    if _model_load_attempted:
        return _nli_cross_encoder

    _model_load_attempted = True
    model_name = getattr(settings, "NLI_MODEL_NAME", "cross-encoder/nli-deberta-v3-base")
    try:
        from sentence_transformers import CrossEncoder
        logger.info(f"Checking for cached local NLI CrossEncoder model: {model_name}...")
        _nli_cross_encoder = CrossEncoder(model_name, local_files_only=True)
        logger.info(f"Loaded cached NLI model: {model_name} successfully.")
    except Exception as e:
        logger.info(
            f"Pretrained NLI model '{model_name}' not cached locally or download disabled ({e}). "
            f"Activating explicitly labeled 'semantic_cosine_rule_fallback' mode."
        )
        _nli_cross_encoder = None

    return _nli_cross_encoder


class ContradictionDetector:
    """
    Classifies statement pairs into CONTRADICTION, ENTAILMENT, or NEUTRAL
    using a local CrossEncoder NLI model with an explicitly labeled fallback mode.
    """

    NLI_LABELS = ["CONTRADICTION", "ENTAILMENT", "NEUTRAL"]

    # Antonym and oppositional polarities for semantic rule fallback
    OPPOSITION_PAIRS = [
        ("eligible", "ineligible"),
        ("approved", "rejected"),
        ("authorized", "unauthorized"),
        ("accepted", "denied"),
        ("allowed", "prohibited"),
        ("permitted", "prohibited"),
        ("permitted", "forbidden"),
        ("mandatory", "optional"),
        ("required", "exempt"),
        ("active", "terminated"),
        ("valid", "invalid"),
        ("compliant", "non-compliant"),
        ("included", "excluded"),
        ("guaranteed", "waived"),
        ("liable", "indemnified"),
        ("increased", "decreased"),
        ("minimum", "maximum"),
        ("internal", "external")
    ]

    NEGATION_MARKERS = {
        "not", "never", "no", "neither", "nor", "cannot", "cant", "won't",
        "prohibited", "forbidden", "disallowed", "terminated", "void", "denied",
        "rejected", "cancelled", "refused", "fails", "without"
    }

    @classmethod
    def classify_pair(cls, statement_a: str, statement_b: str) -> Dict[str, Any]:
        """
        Classifies a single statement pair.
        """
        results = cls.classify_pairs([(statement_a, statement_b)])
        return results[0] if results else {
            "label": "NEUTRAL",
            "confidence": 0.5,
            "probabilities": {"CONTRADICTION": 0.0, "ENTAILMENT": 0.0, "NEUTRAL": 1.0},
            "detection_method": "empty_fallback",
            "fallback_active": True
        }

    @classmethod
    def classify_pairs(cls, pairs: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """
        Classifies multiple statement pairs with batching.
        """
        if not pairs:
            return []

        model = get_nli_model()

        if model is not None:
            try:
                return cls._predict_with_model(model, pairs)
            except Exception as e:
                logger.error(f"Error during NLI model inference: {e}. Reverting to labeled fallback.")

        # Explicitly labeled fallback mode
        return cls._predict_with_fallback(pairs)

    @classmethod
    def _predict_with_model(cls, model, pairs: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """
        Runs batch inference with CrossEncoder and applies softmax over logits.
        Augmented with neuro-symbolic guardrails to prevent polar contradictions
        from being misclassified as entailment.
        """
        batch_size = getattr(settings, "CONSISTENCY_BATCH_SIZE", 16)
        logits = model.predict(pairs, batch_size=batch_size, convert_to_numpy=True)

        id2label = getattr(getattr(model, "model", None), "config", None)
        id_map = getattr(id2label, "id2label", None) if id2label else None
        if id_map:
            label_mapping = {int(k): v.upper() for k, v in id_map.items()}
        else:
            label_mapping = {0: "CONTRADICTION", 1: "ENTAILMENT", 2: "NEUTRAL"}

        results = []
        for i, score_vec in enumerate(logits):
            # Softmax normalization
            exp_scores = np.exp(score_vec - np.max(score_vec))
            probs = exp_scores / exp_scores.sum()

            prob_dict = {
                "CONTRADICTION": 0.0,
                "ENTAILMENT": 0.0,
                "NEUTRAL": 0.0
            }
            for k, lbl in label_mapping.items():
                if k < len(probs):
                    clean_lbl = lbl if lbl in prob_dict else "NEUTRAL"
                    prob_dict[clean_lbl] = round(float(probs[k]), 4)

            best_idx = int(np.argmax(probs))
            raw_label = label_mapping.get(best_idx, "NEUTRAL")
            best_conf = round(float(probs[best_idx]), 4)

            # Neuro-symbolic guardrail: Verify polar oppositions & antonym conflicts
            pair_a, pair_b = pairs[i]
            has_antonym, ant_pair = cls._has_antonym_conflict(pair_a, pair_b)
            has_polarity_flip = (cls._has_negation(pair_a) != cls._has_negation(pair_b))

            if raw_label != "CONTRADICTION" and (has_antonym or (has_polarity_flip and best_conf < 0.96)):
                best_label = "CONTRADICTION"
                best_conf = 0.92 if has_antonym else 0.85
                prob_dict["CONTRADICTION"] = best_conf
                prob_dict["ENTAILMENT"] = round(1.0 - best_conf, 4)
                rationale = (
                    f"Antonym opposition detected ({ant_pair[0]} vs {ant_pair[1]})"
                    if has_antonym
                    else "Direct negation / polarity flip across statements"
                )
            else:
                best_label = raw_label
                rationale = "Local neural CrossEncoder model inference"

            results.append({
                "label": best_label,
                "confidence": best_conf,
                "probabilities": prob_dict,
                "detection_method": "cross_encoder_nli_deberta_v3",
                "fallback_active": False,
                "rationale": rationale
            })

        return results

    @classmethod
    def _predict_with_fallback(cls, pairs: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """
        Explicitly labeled fallback mode:
        Combines dense vector semantic similarity with negation detection,
        antonym pairs, and syntactic opposition.
        """
        results = []

        texts_a = [p[0] for p in pairs]
        texts_b = [p[1] for p in pairs]

        emb_a = EmbeddingService.embed_texts(texts_a)
        emb_b = EmbeddingService.embed_texts(texts_b)

        sims = np.sum(emb_a * emb_b, axis=1) if len(pairs) > 0 else []

        nlp = get_spacy_nlp()

        for idx, (stmt_a, stmt_b) in enumerate(pairs):
            sim = float(sims[idx]) if idx < len(sims) else 0.5
            
            # 1. Analyze Negation & Polarity
            has_neg_a = cls._has_negation(stmt_a, nlp)
            has_neg_b = cls._has_negation(stmt_b, nlp)
            has_polarity_flip = (has_neg_a != has_neg_b)

            # 2. Analyze Antonym / Opposition tokens
            has_antonym_conflict, antonym_pair = cls._has_antonym_conflict(stmt_a, stmt_b)

            # 3. Decision Logic for Fallback
            # Contradiction: High similarity with inverted polarity OR direct antonym conflict
            if (sim >= 0.55 and has_polarity_flip) or has_antonym_conflict:
                conf = 0.85 if has_antonym_conflict else round(0.70 + (sim * 0.20), 4)
                conf = min(0.95, conf)
                results.append({
                    "label": "CONTRADICTION",
                    "confidence": conf,
                    "probabilities": {
                        "CONTRADICTION": conf,
                        "NEUTRAL": round(1.0 - conf, 4),
                        "ENTAILMENT": 0.0
                    },
                    "detection_method": "semantic_cosine_rule_fallback",
                    "fallback_active": True,
                    "rationale": (
                        f"Oppositional keywords detected ({antonym_pair[0]} vs {antonym_pair[1]})"
                        if has_antonym_conflict
                        else "High topical similarity with opposing affirmative/negative polarity"
                    )
                })
            # Entailment: Very high similarity (>= 0.85) without polarity conflict
            elif sim >= 0.85 and not has_polarity_flip:
                conf = round(sim, 4)
                results.append({
                    "label": "ENTAILMENT",
                    "confidence": conf,
                    "probabilities": {
                        "ENTAILMENT": conf,
                        "NEUTRAL": round(1.0 - conf, 4),
                        "CONTRADICTION": 0.0
                    },
                    "detection_method": "semantic_cosine_rule_fallback",
                    "fallback_active": True,
                    "rationale": "High semantic vector alignment without polarity opposition"
                })
            else:
                # Neutral: Distinct statements or unrelated facts
                results.append({
                    "label": "NEUTRAL",
                    "confidence": 0.70,
                    "probabilities": {
                        "NEUTRAL": 0.70,
                        "ENTAILMENT": 0.15,
                        "CONTRADICTION": 0.15
                    },
                    "detection_method": "semantic_cosine_rule_fallback",
                    "fallback_active": True,
                    "rationale": "Independent or non-conflicting assertions"
                })

        return results

    @classmethod
    def _has_negation(cls, text: str, nlp=None) -> bool:
        """
        Detects negation markers via regex or spaCy dependency parsing.
        """
        words = set(re.findall(r"\b[a-zA-Z']+\b", text.lower()))
        if any(neg in words for neg in cls.NEGATION_MARKERS):
            return True

        if nlp:
            try:
                doc = nlp(text)
                for token in doc:
                    if token.dep_ == "neg" or token.lower_ in cls.NEGATION_MARKERS:
                        return True
            except Exception:
                pass

        return False

    @classmethod
    def _has_antonym_conflict(cls, text_a: str, text_b: str) -> Tuple[bool, Optional[Tuple[str, str]]]:
        """
        Checks if text_a contains word X and text_b contains its direct antonym Y.
        """
        tokens_a = set(re.findall(r"\b[a-zA-Z-]+\b", text_a.lower()))
        tokens_b = set(re.findall(r"\b[a-zA-Z-]+\b", text_b.lower()))

        for word_1, word_2 in cls.OPPOSITION_PAIRS:
            if (word_1 in tokens_a and word_2 in tokens_b) or (word_2 in tokens_a and word_1 in tokens_b):
                return True, (word_1, word_2)

        return False, None
