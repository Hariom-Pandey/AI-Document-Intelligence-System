import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class NumericalConsistencyAnalyzer:
    """
    Specialized analyzer for comparing numbers, currencies, dates, durations,
    and percentages across semantically compatible statements.
    """

    REVISION_MARKERS = {
        "revised", "revision", "updated", "update", "amended", "amendment",
        "rescheduled", "postponed", "extended", "adjusted", "superseded",
        "modified", "renegotiated", "new deadline", "latest", "as of"
    }

    SUBJECT_KEYWORDS = {
        "budget", "cost", "price", "fee", "amount", "total", "payment",
        "expense", "revenue", "penalty", "interest", "salary", "stipend",
        "deadline", "completion", "duration", "timeline", "schedule", "period",
        "warranty", "guarantee", "validity", "tenure", "milestone", "delivery", "deliver",
        "deliverable", "report", "contractor", "client", "vendor", "term", "agreement",
        "share", "stake", "equity", "rate", "tax", "commission", "discount"
    }

    @classmethod
    def compare_statements(cls, text_a: str, text_b: str) -> Optional[Dict[str, Any]]:
        """
        Analyzes two statements for numerical or date discrepancies.
        Returns a structured finding dict if a genuine inconsistency is found, or None.
        """
        # 1. Check if statements share a common subject anchor (e.g. budget, deadline, fee)
        shared_subject = cls._extract_shared_subject(text_a, text_b)
        if not shared_subject:
            return None

        # 2. Check for Date Inconsistencies
        date_finding = cls._compare_dates(text_a, text_b, shared_subject)
        if date_finding:
            return date_finding

        # 3. Check for Monetary / Currency Inconsistencies
        money_finding = cls._compare_monetary_values(text_a, text_b, shared_subject)
        if money_finding:
            return money_finding

        # 4. Check for Percentage Inconsistencies
        pct_finding = cls._compare_percentages(text_a, text_b, shared_subject)
        if pct_finding:
            return pct_finding

        # 5. Check for Duration Inconsistencies
        dur_finding = cls._compare_durations(text_a, text_b, shared_subject)
        if dur_finding:
            return dur_finding

        return None

    @classmethod
    def _extract_shared_subject(cls, text_a: str, text_b: str) -> Optional[str]:
        words_a = set(re.findall(r"\b[a-zA-Z]{3,}\b", text_a.lower()))
        words_b = set(re.findall(r"\b[a-zA-Z]{3,}\b", text_b.lower()))

        shared = words_a.intersection(words_b)
        matches = [s for s in cls.SUBJECT_KEYWORDS if s in shared]
        return matches[0] if matches else None

    @classmethod
    def _is_revision(cls, text_a: str, text_b: str) -> bool:
        words = set(re.findall(r"\b[a-zA-Z]+\b", (text_a + " " + text_b).lower()))
        return any(rm in words for rm in cls.REVISION_MARKERS)

    # -------------------------------------------------------------
    # Currency / Monetary Comparison
    # -------------------------------------------------------------
    @classmethod
    def _compare_monetary_values(cls, text_a: str, text_b: str, subject: str) -> Optional[Dict[str, Any]]:
        vals_a = cls._extract_money(text_a)
        vals_b = cls._extract_money(text_b)

        if not vals_a or not vals_b:
            return None

        m_a = vals_a[0]
        m_b = vals_b[0]

        # Incompatible currencies (e.g. INR vs USD)
        if m_a["currency"] != m_b["currency"] and m_a["currency"] != "UNKNOWN" and m_b["currency"] != "UNKNOWN":
            return {
                "conflict_type": "UNRESOLVED_DIFFERENCE",
                "explanation": (
                    f"Different currency units specified for '{subject}': "
                    f"Document A states {m_a['currency']} {m_a['raw']}, "
                    f"while Document B states {m_b['currency']} {m_b['raw']}."
                ),
                "confidence": 0.75,
                "review_status": "needs_review",
                "evidence_context": {
                    "subject": subject,
                    "value_a": m_a["raw"],
                    "value_b": m_b["raw"],
                    "currency_a": m_a["currency"],
                    "currency_b": m_b["currency"],
                    "unit_mismatch": True
                }
            }

        # Check numerical discrepancy
        if abs(m_a["amount"] - m_b["amount"]) > 0.01:
            is_rev = cls._is_revision(text_a, text_b)
            c_type = "POTENTIAL_VERSION_CHANGE" if is_rev else "NUMERICAL_INCONSISTENCY"
            rev_note = " (Flagged as potential revised/amended figure)" if is_rev else ""

            return {
                "conflict_type": c_type,
                "explanation": (
                    f"Conflicting monetary figures for '{subject}': "
                    f"Document A specifies {m_a['raw']}, whereas Document B specifies {m_b['raw']}{rev_note}."
                ),
                "confidence": 0.92 if not is_rev else 0.80,
                "review_status": "needs_review" if is_rev else "confirmed_conflict",
                "evidence_context": {
                    "subject": subject,
                    "value_a": m_a["raw"],
                    "value_b": m_b["raw"],
                    "normalized_a": m_a["amount"],
                    "normalized_b": m_b["amount"],
                    "is_revision": is_rev
                }
            }

        return None

    @classmethod
    def _extract_money(cls, text: str) -> List[Dict[str, Any]]:
        results = []
        # Match currency symbols and figures, e.g. ₹5,00,000, Rs. 50,000, $750,000, 50 Lakhs, 2 Crore
        pattern = r"([₹$€£]|Rs\.?|INR|USD|EUR|GBP)?\s*([\d,]+(?:\.\d+)?)\s*(lakhs?|lacs?|crores?|cr|millions?|m|billion|b|k|thousand)?"
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            curr_sym = match.group(1) or ""
            num_str = match.group(2)
            multiplier_str = match.group(3) or ""

            if not curr_sym and not multiplier_str:
                continue

            cleaned_num = num_str.replace(",", "").strip()
            if not cleaned_num:
                continue

            try:
                base_num = float(cleaned_num)
            except ValueError:
                continue

            # Multiplier expansion
            mult = 1.0
            mult_lower = multiplier_str.lower()
            if "lakh" in mult_lower or "lac" in mult_lower:
                mult = 100000.0
            elif "crore" in mult_lower or "cr" in mult_lower:
                mult = 10000000.0
            elif "million" in mult_lower or mult_lower == "m":
                mult = 1000000.0
            elif "billion" in mult_lower or mult_lower == "b":
                mult = 1000000000.0
            elif "k" in mult_lower or "thousand" in mult_lower:
                mult = 1000.0

            normalized_amt = base_num * mult

            currency = "INR" if any(c in curr_sym.lower() for c in ["₹", "rs", "inr"]) else \
                       "USD" if any(c in curr_sym.lower() for c in ["$", "usd"]) else \
                       "EUR" if any(c in curr_sym.lower() for c in ["€", "eur"]) else \
                       "GBP" if any(c in curr_sym.lower() for c in ["£", "gbp"]) else \
                       ("INR" if ("lakh" in mult_lower or "crore" in mult_lower) else "UNKNOWN")

            results.append({
                "raw": match.group(0).strip(),
                "amount": normalized_amt,
                "currency": currency
            })

        return results

    # -------------------------------------------------------------
    # Date Comparison
    # -------------------------------------------------------------
    @classmethod
    def _compare_dates(cls, text_a: str, text_b: str, subject: str) -> Optional[Dict[str, Any]]:
        dates_a = cls._extract_dates(text_a)
        dates_b = cls._extract_dates(text_b)

        if not dates_a or not dates_b:
            return None

        d_a = dates_a[0]
        d_b = dates_b[0]

        # If date strings match exactly, no conflict
        if d_a["normalized"] == d_b["normalized"]:
            return None

        is_rev = cls._is_revision(text_a, text_b)
        c_type = "POTENTIAL_VERSION_CHANGE" if is_rev else "DATE_INCONSISTENCY"
        rev_note = " (Revised schedule or amended timeline detected)" if is_rev else ""

        return {
            "conflict_type": c_type,
            "explanation": (
                f"Conflicting calendar dates for '{subject}': "
                f"Document A states '{d_a['raw']}', but Document B states '{d_b['raw']}'{rev_note}."
            ),
            "confidence": 0.88 if not is_rev else 0.78,
            "review_status": "needs_review",
            "evidence_context": {
                "subject": subject,
                "date_a": d_a["raw"],
                "date_b": d_b["raw"],
                "normalized_a": d_a["normalized"],
                "normalized_b": d_b["normalized"],
                "is_revision": is_rev
            }
        }

    @classmethod
    def _extract_dates(cls, text: str) -> List[Dict[str, Any]]:
        results = []
        months = r"(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
        
        # 1. "15 December 2026" or "15 Dec 2026"
        p1 = rf"\b(\d{{1,2}})\s+({months})\s+(\d{{4}})\b"
        for m in re.finditer(p1, text, re.IGNORECASE):
            results.append({
                "raw": m.group(0).strip(),
                "normalized": f"{m.group(3)}-{m.group(2).lower()}-{m.group(1).zfill(2)}"
            })

        # 2. "December 15, 2026"
        p2 = rf"\b({months})\s+(\d{{1,2}}),?\s+(\d{{4}})\b"
        for m in re.finditer(p2, text, re.IGNORECASE):
            results.append({
                "raw": m.group(0).strip(),
                "normalized": f"{m.group(3)}-{m.group(1).lower()}-{m.group(2).zfill(2)}"
            })

        # 3. ISO / Slash dates: "2026-12-15" or "15/12/2026"
        p3 = r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b"
        for m in re.finditer(p3, text):
            results.append({
                "raw": m.group(0).strip(),
                "normalized": f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"
            })

        p4 = r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b"
        for m in re.finditer(p4, text):
            results.append({
                "raw": m.group(0).strip(),
                "normalized": f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
            })

        return results

    # -------------------------------------------------------------
    # Percentage Comparison
    # -------------------------------------------------------------
    @classmethod
    def _compare_percentages(cls, text_a: str, text_b: str, subject: str) -> Optional[Dict[str, Any]]:
        pct_pattern = r"\b(\d+(?:\.\d+)?)\s*(?:%|percent)\b"
        matches_a = list(re.finditer(pct_pattern, text_a, re.IGNORECASE))
        matches_b = list(re.finditer(pct_pattern, text_b, re.IGNORECASE))

        if not matches_a or not matches_b:
            return None

        val_a = float(matches_a[0].group(1))
        val_b = float(matches_b[0].group(1))

        if abs(val_a - val_b) > 0.1:
            is_rev = cls._is_revision(text_a, text_b)
            return {
                "conflict_type": "POTENTIAL_VERSION_CHANGE" if is_rev else "NUMERICAL_INCONSISTENCY",
                "explanation": (
                    f"Inconsistent percentage rate for '{subject}': "
                    f"Document A states {val_a}%, while Document B states {val_b}%."
                ),
                "confidence": 0.89,
                "review_status": "needs_review" if is_rev else "confirmed_conflict",
                "evidence_context": {
                    "subject": subject,
                    "percentage_a": f"{val_a}%",
                    "percentage_b": f"{val_b}%",
                    "difference": round(abs(val_a - val_b), 2)
                }
            }

        return None

    # -------------------------------------------------------------
    # Duration Comparison
    # -------------------------------------------------------------
    @classmethod
    def _compare_durations(cls, text_a: str, text_b: str, subject: str) -> Optional[Dict[str, Any]]:
        dur_pattern = r"\b(\d+)\s*(days?|weeks?|months?|years?)\b"
        m_a = list(re.finditer(dur_pattern, text_a, re.IGNORECASE))
        m_b = list(re.finditer(dur_pattern, text_b, re.IGNORECASE))

        if not m_a or not m_b:
            return None

        num_a = int(m_a[0].group(1))
        unit_a = m_a[0].group(2).lower()

        num_b = int(m_b[0].group(1))
        unit_b = m_b[0].group(2).lower()

        # Convert to approximate days
        multiplier = {"day": 1, "days": 1, "week": 7, "weeks": 7, "month": 30, "months": 30, "year": 365, "years": 365}
        days_a = num_a * multiplier.get(unit_a, 1)
        days_b = num_b * multiplier.get(unit_b, 1)

        if days_a != days_b:
            is_rev = cls._is_revision(text_a, text_b)
            return {
                "conflict_type": "POTENTIAL_VERSION_CHANGE" if is_rev else "NUMERICAL_INCONSISTENCY",
                "explanation": (
                    f"Conflicting project duration or timeline for '{subject}': "
                    f"Document A indicates {num_a} {unit_a}, but Document B indicates {num_b} {unit_b}."
                ),
                "confidence": 0.85,
                "review_status": "needs_review",
                "evidence_context": {
                    "subject": subject,
                    "duration_a": f"{num_a} {unit_a}",
                    "duration_b": f"{num_b} {unit_b}"
                }
            }

        return None
