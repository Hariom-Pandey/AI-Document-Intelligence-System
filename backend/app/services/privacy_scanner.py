import re
import logging
from typing import List, Dict, Any, Optional, Set
from app.services.ner import get_spacy_nlp
from app.services.risk_classifier import RiskClassifier

logger = logging.getLogger(__name__)

class PrivacyScanner:
    """
    Comprehensive, privacy-preserving scanner for sensitive personal, statutory,
    and financial information across multi-format documents.
    Combines validated regex patterns, financial/context verification, and spaCy NER.
    """

    # Structured regex patterns
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    
    # Phone numbers: Indian (+91 optional, 10 digits starting 6-9) or formatted International / US
    PHONE_PATTERNS = [
        re.compile(r"(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b"),
        re.compile(r"(?:\+91[\s-]?)?[6-9]\d{9}\b"),
        re.compile(r"\b(?:\+?1[\s-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b"),
        re.compile(r"\b0\d{2,4}[\s-]?\d{6,8}\b")  # Indian landline with STD
    ]

    # Indian Permanent Account Number (PAN)
    PAN_PATTERN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")

    # Indian Aadhaar 12-digit format (first digit cannot be 0 or 1)
    AADHAAR_PATTERN = re.compile(r"\b[2-9]\d{3}[\s-]?\d{4}[\s-]?\d{4}\b")

    # Indian Financial System Code (IFSC)
    IFSC_PATTERN = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")

    # Credit / Debit Cards (13 to 19 digits formatted in groups of 4)
    CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")

    # Passport patterns
    PASSPORT_PATTERN = re.compile(r"\b[A-PR-WYa-pr-wy][1-9]\d\s?\d{4}[1-9]\b")
    GENERIC_PASSPORT_PATTERN = re.compile(r"\b[A-Z][0-9]{7,8}\b")

    # Bank Account numbers (9 to 18 digits)
    BANK_ACCOUNT_PATTERN = re.compile(r"\b\d{9,18}\b")

    @classmethod
    def scan_document(
        cls,
        full_text: str,
        pages: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes a comprehensive privacy scan over document pages or text.
        Returns a deduplicated, page-indexed list of structured privacy findings.
        """
        if (not full_text or not full_text.strip()) and not pages:
            return []

        findings: List[Dict[str, Any]] = []

        if pages and len(pages) > 0:
            for page in pages:
                p_num = page.get("page_number", 1)
                p_text = page.get("text", "")
                if p_text.strip():
                    page_findings = cls._scan_text_unit(p_text, page_number=p_num)
                    findings.extend(page_findings)
        else:
            findings = cls._scan_text_unit(full_text, page_number=1)

        # Global deduplication by (entity_type, raw_value, page_number)
        seen_keys: Set[str] = set()
        deduped: List[Dict[str, Any]] = []

        for f in findings:
            key = f"{f['entity_type']}::{f['raw_value'].strip().lower()}::p{f['page_number']}"
            if key not in seen_keys:
                seen_keys.add(key)
                deduped.append(f)

        return deduped

    @classmethod
    def _scan_text_unit(cls, text: str, page_number: int = 1) -> List[Dict[str, Any]]:
        """
        Scans a single page or text unit for all supported sensitive entity archetypes.
        """
        findings = []

        # 1. Emails
        for m in cls.EMAIL_PATTERN.finditer(text):
            val = m.group(0).strip()
            # Basic validation
            if len(val) >= 6 and not val.endswith(".png") and not val.endswith(".jpg"):
                ctx = cls._get_context_window(text, m.start(), m.end())
                risk_info = RiskClassifier.classify_risk("EMAIL", val, context=ctx)
                findings.append({
                    "entity_type": "EMAIL",
                    "raw_value": val,
                    "masked_value": RiskClassifier.mask_value(val, "EMAIL"),
                    "risk_level": risk_info["risk_level"],
                    "detection_method": "regex_pattern_validated",
                    "confidence": 0.99,
                    "page_number": page_number,
                    "start_char": m.start(),
                    "end_char": m.end(),
                    "explanation": risk_info["explanation"],
                    "review_status": "needs_review",
                    "is_redacted": False
                })

        # 2. PAN Card
        for m in cls.PAN_PATTERN.finditer(text):
            val = m.group(0).strip()
            # 4th character validation: P=Individual, C=Company, H=HUF, F=Firm, A=AOP, T=Trust, etc.
            fourth_char = val[3].upper()
            valid_fourth = fourth_char in "PCHFATBLJG"
            ctx = cls._get_context_window(text, m.start(), m.end())
            has_pan_context = any(k in ctx.lower() for k in ["pan", "tax", "income", "permanent account", "nsdl", "uti", "card", "identity", "number", "id"])
            
            # 5 letters + 4 digits + 1 letter is highly distinctive
            conf = 0.98 if (valid_fourth or has_pan_context) else 0.88
            risk_info = RiskClassifier.classify_risk("PAN_CARD", val, context=ctx)
            findings.append({
                "entity_type": "PAN_CARD",
                "raw_value": val,
                "masked_value": RiskClassifier.mask_value(val, "PAN_CARD"),
                "risk_level": "HIGH",
                "detection_method": "regex_pattern_validated",
                "confidence": conf,
                "page_number": page_number,
                "start_char": m.start(),
                "end_char": m.end(),
                "explanation": "Detected Indian Permanent Account Number (PAN) statutory tax identifier.",
                "review_status": "needs_review",
                "is_redacted": False
            })

        # 3. Aadhaar Number
        for m in cls.AADHAAR_PATTERN.finditer(text):
            val = m.group(0).strip()
            digits = re.sub(r"\D", "", val)
            if len(digits) == 12:
                # Discard sequential or repetitive mock test patterns (e.g. 000000000000)
                if len(set(digits)) > 2:
                    ctx = cls._get_context_window(text, m.start(), m.end())
                    has_aadhaar_ctx = any(k in ctx.lower() for k in ["aadhaar", "aadhar", "uid", "uidai", "identity", "id no", "unique identification"])
                    conf = 0.96 if has_aadhaar_ctx else 0.82
                    risk_info = RiskClassifier.classify_risk("AADHAAR", val, context=ctx)
                    findings.append({
                        "entity_type": "AADHAAR",
                        "raw_value": val,
                        "masked_value": RiskClassifier.mask_value(val, "AADHAAR"),
                        "risk_level": "HIGH",
                        "detection_method": "regex_pattern_validated",
                        "confidence": conf,
                        "page_number": page_number,
                        "start_char": m.start(),
                        "end_char": m.end(),
                        "explanation": "Potential 12-digit Indian Aadhaar national identification sequence.",
                        "review_status": "needs_review",
                        "is_redacted": False
                    })

        # 4. IFSC Code
        for m in cls.IFSC_PATTERN.finditer(text):
            val = m.group(0).strip()
            # 5th char must be zero
            if val[4] == "0":
                ctx = cls._get_context_window(text, m.start(), m.end())
                risk_info = RiskClassifier.classify_risk("IFSC_CODE", val, context=ctx)
                findings.append({
                    "entity_type": "IFSC_CODE",
                    "raw_value": val,
                    "masked_value": RiskClassifier.mask_value(val, "IFSC_CODE"),
                    "risk_level": "MEDIUM",
                    "detection_method": "regex_pattern_validated",
                    "confidence": 0.95,
                    "page_number": page_number,
                    "start_char": m.start(),
                    "end_char": m.end(),
                    "explanation": "Indian Financial System Code (IFSC) used for banking routing and electronic transfers.",
                    "review_status": "needs_review",
                    "is_redacted": False
                })

        # 5. Phone Numbers
        for pat in cls.PHONE_PATTERNS:
            for m in pat.finditer(text):
                val = m.group(0).strip()
                digits = re.sub(r"\D", "", val)
                # Discard pure timestamps or year strings (e.g. 2024, 1998)
                if len(digits) >= 10 and len(digits) <= 13:
                    # Filter out obvious false positives like git hashes or ISO dates
                    ctx = cls._get_context_window(text, m.start(), m.end())
                    ctx_lower = ctx.lower()
                    
                    # Avoid flagging dates like 2026-11-13
                    if "-" in val and len(val.split("-")[0]) == 4:
                        continue
                    
                    has_phone_context = any(k in ctx_lower for k in [
                        "phone", "mobile", "cell", "tel", "call", "contact", "m:", "whatsapp", "+91", "reach me at"
                    ])
                    conf = 0.96 if has_phone_context else 0.85
                    risk_info = RiskClassifier.classify_risk("PHONE", val, context=ctx)
                    findings.append({
                        "entity_type": "PHONE",
                        "raw_value": val,
                        "masked_value": RiskClassifier.mask_value(val, "PHONE"),
                        "risk_level": risk_info["risk_level"],
                        "detection_method": "regex_pattern_validated",
                        "confidence": conf,
                        "page_number": page_number,
                        "start_char": m.start(),
                        "end_char": m.end(),
                        "explanation": risk_info["explanation"],
                        "review_status": "needs_review",
                        "is_redacted": False
                    })

        # 6. Credit / Debit Cards with Luhn Check
        for m in cls.CARD_PATTERN.finditer(text):
            val = m.group(0).strip()
            digits = re.sub(r"\D", "", val)
            if len(digits) == 16 and cls._luhn_checksum(digits):
                ctx = cls._get_context_window(text, m.start(), m.end())
                risk_info = RiskClassifier.classify_risk("CREDIT_CARD", val, context=ctx)
                findings.append({
                    "entity_type": "CREDIT_CARD",
                    "raw_value": val,
                    "masked_value": RiskClassifier.mask_value(val, "CREDIT_CARD"),
                    "risk_level": "HIGH",
                    "detection_method": "regex_luhn_verified",
                    "confidence": 0.99,
                    "page_number": page_number,
                    "start_char": m.start(),
                    "end_char": m.end(),
                    "explanation": "Luhn-validated 16-digit payment card number.",
                    "review_status": "needs_review",
                    "is_redacted": False
                })

        # 7. Bank Account Numbers (requires financial context words to reduce false positives)
        for m in cls.BANK_ACCOUNT_PATTERN.finditer(text):
            val = m.group(0).strip()
            # Avoid matching card numbers or 10-digit phone numbers
            if len(val) in [10, 16]:
                # Handled by Phone / Card scanners
                continue
            
            ctx = cls._get_context_window(text, m.start(), m.end(), window=80)
            ctx_lower = ctx.lower()
            financial_keywords = [
                "account", "a/c", "acct", "savings", "current", "bank", "beneficiary",
                "credited", "debited", "branch", "deposit", "acc no", "account no"
            ]
            if any(k in ctx_lower for k in financial_keywords):
                risk_info = RiskClassifier.classify_risk("BANK_ACCOUNT", val, context=ctx)
                findings.append({
                    "entity_type": "BANK_ACCOUNT",
                    "raw_value": val,
                    "masked_value": RiskClassifier.mask_value(val, "BANK_ACCOUNT"),
                    "risk_level": "HIGH",
                    "detection_method": "contextual_financial_rule",
                    "confidence": 0.92,
                    "page_number": page_number,
                    "start_char": m.start(),
                    "end_char": m.end(),
                    "explanation": f"Bank account number identified alongside financial context.",
                    "review_status": "needs_review",
                    "is_redacted": False
                })

        # 8. Passports
        for m in cls.PASSPORT_PATTERN.finditer(text):
            val = m.group(0).strip()
            ctx = cls._get_context_window(text, m.start(), m.end())
            has_passport_context = any(k in ctx.lower() for k in ["passport", "travel", "nationality", "republic of india", "issuing"])
            if has_passport_context:
                risk_info = RiskClassifier.classify_risk("PASSPORT", val, context=ctx)
                findings.append({
                    "entity_type": "PASSPORT",
                    "raw_value": val,
                    "masked_value": RiskClassifier.mask_value(val, "PASSPORT"),
                    "risk_level": "HIGH",
                    "detection_method": "regex_pattern_validated",
                    "confidence": 0.94,
                    "page_number": page_number,
                    "start_char": m.start(),
                    "end_char": m.end(),
                    "explanation": "Passport identity travel document number.",
                    "review_status": "needs_review",
                    "is_redacted": False
                })

        # 9. spaCy NER for Names & Addresses
        nlp = get_spacy_nlp()
        if nlp:
            try:
                # Process text with spaCy (up to 100k chars per page)
                doc = nlp(text[:100000])
                for ent in doc.ents:
                    ent_text = ent.text.strip()
                    if not ent_text or len(ent_text) < 3:
                        continue

                    if ent.label_ == "PERSON":
                        # Filter out common false positive stop words or tech terms
                        if ent_text.lower() not in {"github", "linkedin", "python", "react", "fastapi", "docker", "flutter", "unit", "section"}:
                            ctx = cls._get_context_window(text, ent.start_char, ent.end_char)
                            risk_info = RiskClassifier.classify_risk("PERSON_NAME", ent_text, context=ctx)
                            findings.append({
                                "entity_type": "PERSON_NAME",
                                "raw_value": ent_text,
                                "masked_value": RiskClassifier.mask_value(ent_text, "PERSON_NAME"),
                                "risk_level": risk_info["risk_level"],
                                "detection_method": "spacy_ner_model",
                                "confidence": 0.88,
                                "page_number": page_number,
                                "start_char": ent.start_char,
                                "end_char": ent.end_char,
                                "explanation": risk_info["explanation"],
                                "review_status": "needs_review",
                                "is_redacted": False
                            })

                    elif ent.label_ in ["GPE", "LOC", "FAC"]:
                        # Address detection: check if accompanied by street/residential keywords
                        ctx = cls._get_context_window(text, ent.start_char, ent.end_char, window=60)
                        address_cues = ["flat", "house", "street", "road", "sector", "lane", "nagar", "apartment", "pin", "zip", "colony", "block"]
                        if any(c in ctx.lower() for c in address_cues):
                            full_address = ctx.strip()
                            risk_info = RiskClassifier.classify_risk("ADDRESS", ent_text, context=ctx)
                            findings.append({
                                "entity_type": "ADDRESS",
                                "raw_value": ent_text,
                                "masked_value": RiskClassifier.mask_value(ent_text, "ADDRESS"),
                                "risk_level": "MEDIUM",
                                "detection_method": "spacy_context_rule",
                                "confidence": 0.80,
                                "page_number": page_number,
                                "start_char": ent.start_char,
                                "end_char": ent.end_char,
                                "explanation": "Physical or residential location cue identified.",
                                "review_status": "needs_review",
                                "is_redacted": False
                            })
            except Exception as e:
                logger.warning(f"spaCy privacy scan pass encountered error: {e}")

        return findings

    @staticmethod
    def _get_context_window(text: str, start: int, end: int, window: int = 50) -> str:
        ctx_start = max(0, start - window)
        ctx_end = min(len(text), end + window)
        return text[ctx_start:ctx_end]

    @staticmethod
    def _luhn_checksum(digits_str: str) -> bool:
        """
        Validates Luhn algorithm for credit card numbers.
        """
        try:
            digits = [int(c) for c in digits_str]
            checksum = 0
            reverse_digits = digits[::-1]
            for i, d in enumerate(reverse_digits):
                if i % 2 == 1:
                    doubled = d * 2
                    checksum += (doubled - 9) if doubled > 9 else doubled
                else:
                    checksum += d
            return checksum % 10 == 0
        except Exception:
            return False

    @classmethod
    def generate_privacy_report(
        cls,
        findings: List[Dict[str, Any]],
        document_id: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Aggregates individual findings into an executive privacy risk report.
        """
        total = len(findings)
        high_risk = sum(1 for f in findings if f.get("risk_level") == "HIGH")
        medium_risk = sum(1 for f in findings if f.get("risk_level") == "MEDIUM")
        low_risk = sum(1 for f in findings if f.get("risk_level") == "LOW")

        # Category distribution
        categories: Dict[str, int] = {}
        for f in findings:
            cat = f.get("entity_type", "OTHER")
            categories[cat] = categories.get(cat, 0) + 1

        # Page distribution
        pages: Dict[int, int] = {}
        for f in findings:
            pg = f.get("page_number", 1)
            pages[pg] = pages.get(pg, 0) + 1

        # Overall risk level
        if high_risk > 0:
            overall_risk = "CRITICAL" if high_risk >= 3 else "HIGH"
        elif medium_risk > 0:
            overall_risk = "MODERATE"
        elif low_risk > 0:
            overall_risk = "LOW"
        else:
            overall_risk = "CLEAN"

        recommendations = RiskClassifier.generate_recommendations(findings)

        return {
            "document_id": document_id,
            "filename": filename,
            "total_findings": total,
            "risk_summary": {
                "high": high_risk,
                "medium": medium_risk,
                "low": low_risk,
                "overall_risk": overall_risk
            },
            "category_distribution": categories,
            "page_distribution": pages,
            "recommended_actions": recommendations,
            "findings": findings
        }
