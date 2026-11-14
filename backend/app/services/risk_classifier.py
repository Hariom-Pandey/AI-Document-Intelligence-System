import re
from typing import Dict, Any, List

class RiskClassifier:
    """
    Context-aware risk classification engine for sensitive and privacy-related findings.
    Classifies findings into HIGH, MEDIUM, or LOW risk with explainable rationales and recommended actions.
    """

    # Baseline entity risk mappings
    RISK_LEVEL_MAP = {
        "AADHAAR": "HIGH",
        "PAN_CARD": "HIGH",
        "PASSPORT": "HIGH",
        "BANK_ACCOUNT": "HIGH",
        "CREDIT_CARD": "HIGH",
        "SSN": "HIGH",
        "PHONE": "MEDIUM",
        "EMAIL": "MEDIUM",
        "IFSC_CODE": "MEDIUM",
        "ADDRESS": "MEDIUM",
        "PERSON_NAME": "LOW",
        "ORGANIZATION": "LOW",
        "DATE_OF_BIRTH": "MEDIUM",
    }

    @classmethod
    def classify_risk(
        cls,
        entity_type: str,
        value: str,
        context: str = "",
        confidence: float = 1.0
    ) -> Dict[str, Any]:
        """
        Determines the risk level and provides an explainable rationale based on entity type and surrounding context.
        """
        base_level = cls.RISK_LEVEL_MAP.get(entity_type, "MEDIUM")
        context_lower = context.lower()
        explanation = ""

        # Context-aware adjustments
        if entity_type == "PERSON_NAME":
            if any(k in context_lower for k in ["confidential", "plaintiff", "defendant", "patient", "victim", "salary", "ssn"]):
                base_level = "MEDIUM"
                explanation = "Person name appears in a sensitive or confidential context."
            else:
                base_level = "LOW"
                explanation = "General person name identified in document text."

        elif entity_type == "EMAIL":
            if any(k in context_lower for k in ["personal", "contact", "mobile", "home", "private"]):
                base_level = "MEDIUM"
                explanation = "Direct personal or direct communication email address."
            else:
                base_level = "MEDIUM"
                explanation = "Email address exposed in document."

        elif entity_type == "PHONE":
            base_level = "MEDIUM"
            explanation = "Direct mobile or telephone number susceptible to unsolicited contact."

        elif entity_type == "PAN_CARD":
            base_level = "HIGH"
            explanation = "Permanent Account Number (PAN) is a sensitive statutory tax and financial identifier."

        elif entity_type == "AADHAAR":
            base_level = "HIGH"
            explanation = "Aadhaar number is a unique statutory national identity identifier subject to strict data protection regulations."

        elif entity_type == "BANK_ACCOUNT":
            base_level = "HIGH"
            explanation = "Bank account number exposes direct financial transaction capabilities."

        elif entity_type == "CREDIT_CARD":
            base_level = "HIGH"
            explanation = "Payment card number subject to PCI-DSS data protection requirements."

        elif entity_type == "PASSPORT":
            base_level = "HIGH"
            explanation = "International travel identity document containing government-verified personal credentials."

        elif entity_type == "IFSC_CODE":
            base_level = "MEDIUM"
            explanation = "Bank branch identifier frequently paired with account numbers for fund transfers."

        elif entity_type == "ADDRESS":
            base_level = "MEDIUM"
            explanation = "Physical or residential address revealing geographical location."

        else:
            explanation = f"Potential sensitive entity of type {entity_type}."

        return {
            "risk_level": base_level,
            "explanation": explanation
        }

    @classmethod
    def mask_value(cls, value: str, entity_type: str) -> str:
        """
        Masks sensitive characters for safe user-interface presentation and report summaries.
        Avoids exposing raw credentials while maintaining enough context for user identification.
        """
        if not value:
            return ""

        v = value.strip()

        if entity_type == "EMAIL":
            if "@" in v:
                user, domain = v.split("@", 1)
                if len(user) <= 2:
                    masked_user = user[0] + "*"
                else:
                    masked_user = user[0] + "*" * (len(user) - 2) + user[-1]
                return f"{masked_user}@{domain}"
            return v[:2] + "****"

        elif entity_type == "PHONE":
            # Keep country code if present and last 2 digits
            digits_only = re.sub(r"\D", "", v)
            if len(digits_only) >= 10:
                last_two = digits_only[-2:]
                prefix = v[:len(v) - len(digits_only) + 4] if len(v) > 6 else v[:3]
                return f"{prefix}****{last_two}"
            return v[:3] + "****" + v[-2:] if len(v) > 5 else "****"

        elif entity_type == "PAN_CARD":
            # PAN is 10 chars: ABCDE1234F -> ABCD****4F
            if len(v) == 10:
                return f"{v[:4]}****{v[-2:]}"
            return v[:2] + "****" + v[-1:]

        elif entity_type == "AADHAAR":
            # 12 digits: 1234 5678 9012 -> **** **** 9012
            digits_only = re.sub(r"\D", "", v)
            if len(digits_only) == 12:
                return f"**** **** {digits_only[-4:]}"
            return "**** **** " + v[-4:] if len(v) >= 4 else "************"

        elif entity_type == "BANK_ACCOUNT":
            digits_only = re.sub(r"\D", "", v)
            if len(digits_only) >= 4:
                return f"A/C ********{digits_only[-4:]}"
            return "A/C ********"

        elif entity_type == "CREDIT_CARD":
            digits_only = re.sub(r"\D", "", v)
            if len(digits_only) >= 4:
                return f"****-****-****-{digits_only[-4:]}"
            return "****-****-****-****"

        elif entity_type == "PASSPORT":
            if len(v) >= 4:
                return f"{v[:2]}****{v[-1:]}"
            return v[:1] + "****"

        elif entity_type == "IFSC_CODE":
            if len(v) == 11:
                return f"{v[:4]}0****{v[-2:]}"
            return v[:4] + "****"

        elif entity_type == "PERSON_NAME":
            words = v.split()
            masked_words = []
            for w in words:
                if len(w) <= 2:
                    masked_words.append(w[0] + "*")
                else:
                    masked_words.append(w[0] + "*" * (len(w) - 1))
            return " ".join(masked_words)

        elif entity_type == "ADDRESS":
            parts = [p.strip() for p in v.split(",") if p.strip()]
            if len(parts) > 1:
                return f"[Address: {parts[0][:3]}***, {parts[-1]}]"
            return v[:6] + "********"

        # General fallback masking
        if len(v) <= 4:
            return "*" * len(v)
        return v[:2] + "*" * (len(v) - 4) + v[-2:]

    @classmethod
    def generate_recommendations(cls, findings: List[Dict[str, Any]]) -> List[str]:
        """
        Synthesizes human-actionable security recommendations based on detected findings.
        """
        if not findings:
            return ["No sensitive personal or financial information detected. Document is low risk for public sharing."]

        recommendations = []
        high_risk_count = sum(1 for f in findings if f.get("risk_level") == "HIGH")
        medium_risk_count = sum(1 for f in findings if f.get("risk_level") == "MEDIUM")
        types_detected = {f.get("entity_type") for f in findings}

        if high_risk_count > 0:
            recommendations.append(
                f"Critical: Found {high_risk_count} high-risk identifier(s) (including {', '.join([t for t in types_detected if cls.RISK_LEVEL_MAP.get(t) == 'HIGH'])}) that should be permanently redacted prior to distribution."
            )

        if "AADHAAR" in types_detected or "PAN_CARD" in types_detected or "PASSPORT" in types_detected:
            recommendations.append(
                "Government identifiers subject to statutory privacy compliance (e.g. Aadhaar Act / DPDP / GDPR) were identified. Apply irreversible redaction."
            )

        if "BANK_ACCOUNT" in types_detected or "CREDIT_CARD" in types_detected:
            recommendations.append(
                "Direct financial payment information detected. Ensure these details are confirmed and redacted to prevent financial exposure."
            )

        if "PHONE" in types_detected or "EMAIL" in types_detected:
            recommendations.append(
                f"Detected {sum(1 for f in findings if f.get('entity_type') in ['PHONE', 'EMAIL'])} direct communication endpoint(s). Review and mask to prevent unsolicited communications."
            )

        if not recommendations:
            recommendations.append("Review detected entities and mark any confirmed sensitive entries for permanent sanitization.")

        return recommendations

