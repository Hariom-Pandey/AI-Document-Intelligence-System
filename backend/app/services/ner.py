import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

_spacy_nlp = None

def get_spacy_nlp():
    global _spacy_nlp
    if _spacy_nlp is None:
        try:
            import spacy
            _spacy_nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy en_core_web_sm model.")
        except Exception as e:
            logger.warning(f"Failed to load spaCy model: {e}. Falling back to rule-based NER.")
            _spacy_nlp = False
    return _spacy_nlp

class EntityExtractor:
    """
    Extracts named entities (PERSON, ORG, GPE, DATE, MONEY, etc.)
    using spaCy with an intelligent rule-based fallback.
    """

    @staticmethod
    def extract_entities(text: str, pages: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not text or not text.strip():
            return []

        nlp = get_spacy_nlp()
        if nlp:
            try:
                return EntityExtractor._extract_spacy(nlp, text, pages)
            except Exception as e:
                logger.error(f"spaCy extraction error: {e}. Using regex fallback.")
        
        return EntityExtractor._extract_fallback(text, pages)

    @staticmethod
    def _extract_spacy(nlp, text: str, pages: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # Process in chunks of max 200,000 characters to stay within memory limits
        max_chars = 150000
        sample_text = text[:max_chars]
        doc = nlp(sample_text)

        raw_entities = []
        seen = set()

        # Build page offset mapping if pages provided
        page_offsets = []
        if pages:
            cum_len = 0
            for p in pages:
                p_len = len(p.get("text", ""))
                page_offsets.append((cum_len, cum_len + p_len, p.get("page_number", 1)))
                cum_len += p_len + 2

        for ent in doc.ents:
            ent_text = ent.text.strip()
            # Filter single character or noisy tokens
            if len(ent_text) <= 1 or ent_text.isdigit() or not re.search(r"\w", ent_text):
                continue

            key = (ent_text.lower(), ent.label_)
            if key in seen:
                continue
            seen.add(key)

            # Determine page number
            page_num = 1
            if page_offsets:
                for start, end, p_num in page_offsets:
                    if start <= ent.start_char <= end:
                        page_num = p_num
                        break

            raw_entities.append({
                "text": ent_text,
                "label": ent.label_,
                "start_char": ent.start_char,
                "end_char": ent.end_char,
                "page_number": page_num
            })

        # Sort by label then length
        return sorted(raw_entities, key=lambda x: (x["label"], x["text"]))

    @staticmethod
    def _extract_fallback(text: str, pages: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Regex patterns for DATE, EMAIL, MONEY, and capitalized entities.
        """
        entities = []
        seen = set()

        # Date pattern
        date_pattern = r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4})\b"
        for match in re.finditer(date_pattern, text, re.IGNORECASE):
            val = match.group().strip()
            if val.lower() not in seen:
                seen.add(val.lower())
                entities.append({
                    "text": val,
                    "label": "DATE",
                    "start_char": match.start(),
                    "end_char": match.end(),
                    "page_number": 1
                })

        # Money pattern
        money_pattern = r"(?:[\$€£₹]\s*\d+(?:,\d{3})*(?:\.\d+)?|\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:USD|EUR|GBP|INR|dollars|cents)\b)"
        for match in re.finditer(money_pattern, text):
            val = match.group().strip()
            if val.lower() not in seen:
                seen.add(val.lower())
                entities.append({
                    "text": val,
                    "label": "MONEY",
                    "start_char": match.start(),
                    "end_char": match.end(),
                    "page_number": 1
                })

        # Organization / Proper Names pattern (2-4 capitalized words)
        org_pattern = r"\b[A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){1,3}\b"
        for match in re.finditer(org_pattern, text):
            val = match.group().strip()
            if len(val) > 3 and val.lower() not in seen:
                seen.add(val.lower())
                entities.append({
                    "text": val,
                    "label": "ORG",
                    "start_char": match.start(),
                    "end_char": match.end(),
                    "page_number": 1
                })

        return entities[:100]

