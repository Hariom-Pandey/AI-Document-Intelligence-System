from app.services.nlp import local_nli_relation
from app.services.privacy import scan_sensitive_info


def test_sensitive_scan_detects_core_patterns():
    text = "Contact Hariom Pandey at hariom@example.com, PAN ABCDE1234F, Aadhaar 1234 5678 9123, IFSC HDFC0001234."
    findings = scan_sensitive_info(text, [{"page_number": 1, "text": text}], [{"text": "Hariom Pandey", "label": "PERSON"}])

    types = {f.info_type for f in findings}
    assert "Email" in types
    assert "PAN-like" in types
    assert "Aadhaar-like" in types
    assert "IFSC" in types
    assert "Person" in types


def test_local_nli_flags_budget_contradiction():
    relation, score, reason = local_nli_relation(
        "The project budget is ₹10 lakh.",
        "The project budget is ₹15 lakh.",
    )
    assert relation == "Contradiction"
    assert score > 0.5
    assert "inconsistency" in reason.lower() or "contradiction" in reason.lower()
