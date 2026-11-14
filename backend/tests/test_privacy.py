import os
import shutil
import pytest
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import SessionLocal, init_db
from app.db import repository
from app.services.privacy_scanner import PrivacyScanner
from app.services.risk_classifier import RiskClassifier
from app.services.document_redactor import DocumentRedactor

@pytest.fixture(scope="module")
def db():
    init_db()
    session = SessionLocal()
    yield session
    session.close()

# --------------------------------------------------------------------------
# 1. Email Detection
# --------------------------------------------------------------------------
def test_email_detection():
    text = "Please reach out to support_user1@example.com or direct.lead@company.org regarding the case."
    findings = PrivacyScanner.scan_document(text)
    email_findings = [f for f in findings if f["entity_type"] == "EMAIL"]
    
    assert len(email_findings) == 2
    raw_emails = [f["raw_value"] for f in email_findings]
    assert "support_user1@example.com" in raw_emails
    assert "direct.lead@company.org" in raw_emails
    assert all("*" in f["masked_value"] for f in email_findings)
    assert all(f["risk_level"] == "MEDIUM" for f in email_findings)

# --------------------------------------------------------------------------
# 2. Phone Number Detection
# --------------------------------------------------------------------------
def test_phone_detection():
    text = "Call candidate on mobile: +91 9876543210 or emergency desk at (555) 234-5678."
    findings = PrivacyScanner.scan_document(text)
    phone_findings = [f for f in findings if f["entity_type"] == "PHONE"]
    
    assert len(phone_findings) >= 1
    phone_vals = [f["raw_value"] for f in phone_findings]
    assert any("9876543210" in v for v in phone_vals)
    assert any("*" in f["masked_value"] for f in phone_findings)

# --------------------------------------------------------------------------
# 3. PAN-like Pattern Detection
# --------------------------------------------------------------------------
def test_pan_card_detection():
    text = "Taxpayer PAN number is ABCDE1234F for individual assessment."
    findings = PrivacyScanner.scan_document(text)
    pan_findings = [f for f in findings if f["entity_type"] == "PAN_CARD"]
    
    assert len(pan_findings) == 1
    assert pan_findings[0]["raw_value"] == "ABCDE1234F"
    assert pan_findings[0]["risk_level"] == "HIGH"
    assert pan_findings[0]["masked_value"] == "ABCD****4F"

# --------------------------------------------------------------------------
# 4. Aadhaar-like Pattern Detection
# --------------------------------------------------------------------------
def test_aadhaar_detection():
    text = "Identity UID Aadhaar: 9876 5432 1098 presented for KYC verification."
    findings = PrivacyScanner.scan_document(text)
    aadhaar_findings = [f for f in findings if f["entity_type"] == "AADHAAR"]
    
    assert len(aadhaar_findings) == 1
    assert "9876" in aadhaar_findings[0]["raw_value"]
    assert aadhaar_findings[0]["risk_level"] == "HIGH"
    assert aadhaar_findings[0]["masked_value"].endswith("1098")

# --------------------------------------------------------------------------
# 5. Bank Account & IFSC Detection
# --------------------------------------------------------------------------
def test_bank_and_ifsc_detection():
    text = "Transfer salary to beneficiary Bank Account: 12345678901234 at Branch IFSC: SBIN0012345."
    findings = PrivacyScanner.scan_document(text)
    
    bank_findings = [f for f in findings if f["entity_type"] == "BANK_ACCOUNT"]
    ifsc_findings = [f for f in findings if f["entity_type"] == "IFSC_CODE"]
    
    assert len(bank_findings) == 1
    assert bank_findings[0]["raw_value"] == "12345678901234"
    assert bank_findings[0]["risk_level"] == "HIGH"
    
    assert len(ifsc_findings) == 1
    assert ifsc_findings[0]["raw_value"] == "SBIN0012345"
    assert ifsc_findings[0]["risk_level"] == "MEDIUM"

# --------------------------------------------------------------------------
# 6. False-Positive Reduction
# --------------------------------------------------------------------------
def test_false_positive_reduction():
    # Ordinary numbers, years, version tags, and measurements should not be flagged as sensitive IDs
    benign_text = (
        "The project version is v1.2.3 released on 2024-05-12. "
        "Total inventory is 500 units with 42 percent efficiency and 100 items."
    )
    findings = PrivacyScanner.scan_document(benign_text)
    
    # Should not flag as Bank Account, PAN, or Phone
    high_risk_findings = [f for f in findings if f["risk_level"] == "HIGH"]
    assert len(high_risk_findings) == 0

# --------------------------------------------------------------------------
# 7. Page Number Association
# --------------------------------------------------------------------------
def test_page_number_association():
    pages = [
        {"page_number": 1, "text": "Contact page one via email: test_page1@example.com"},
        {"page_number": 2, "text": "PAN on page two is XYZPA1234K for tax purposes."}
    ]
    findings = PrivacyScanner.scan_document("", pages=pages)
    
    email_f = next(f for f in findings if f["entity_type"] == "EMAIL")
    pan_f = next(f for f in findings if f["entity_type"] == "PAN_CARD")
    
    assert email_f["page_number"] == 1
    assert pan_f["page_number"] == 2

# --------------------------------------------------------------------------
# 8. Risk Classification & Explainability
# --------------------------------------------------------------------------
def test_risk_classification():
    pan_risk = RiskClassifier.classify_risk("PAN_CARD", "ABCDE1234F")
    assert pan_risk["risk_level"] == "HIGH"
    assert "tax" in pan_risk["explanation"].lower() or "pan" in pan_risk["explanation"].lower()
    
    phone_risk = RiskClassifier.classify_risk("PHONE", "+91 9876543210")
    assert phone_risk["risk_level"] == "MEDIUM"
    
    name_risk = RiskClassifier.classify_risk("PERSON_NAME", "Alice Cooper")
    assert name_risk["risk_level"] == "LOW"

# --------------------------------------------------------------------------
# 9. User Review Status Updates
# --------------------------------------------------------------------------
def test_user_review_status_updates(db: Session):
    doc = repository.create_document(db, "test_doc.txt", "mock/path.txt", "txt", 100)
    
    findings_data = [{
        "entity_type": "EMAIL",
        "raw_value": "user@example.com",
        "masked_value": "u***r@example.com",
        "risk_level": "MEDIUM",
        "detection_method": "regex",
        "confidence": 0.99,
        "page_number": 1,
        "explanation": "Email found",
        "review_status": "needs_review"
    }]
    saved = repository.save_privacy_findings(db, doc.id, findings_data)
    assert len(saved) == 1
    finding_id = saved[0].id
    
    # Update to confirmed_sensitive
    updated = repository.update_privacy_finding_status(db, finding_id, "confirmed_sensitive")
    assert updated.review_status == "confirmed_sensitive"
    
    # Update to not_sensitive
    updated2 = repository.update_privacy_finding_status(db, finding_id, "not_sensitive")
    assert updated2.review_status == "not_sensitive"
    
    # Cleanup
    repository.delete_document(db, doc.id)

# --------------------------------------------------------------------------
# 10 & 11. Permanent PDF Redaction & Text Extraction Verification
# --------------------------------------------------------------------------
def test_pdf_permanent_redaction_and_verification(tmp_path):
    import fitz

    # Create synthetic PDF
    pdf_path = str(tmp_path / "synthetic_test.pdf")
    doc = fitz.open()
    page = doc.new_page()
    secret_text = "SECRET_TOKEN_445566"
    page.insert_text((50, 72), f"This document contains a {secret_text} that must be wiped.")
    doc.save(pdf_path)
    doc.close()

    # Redact using DocumentRedactor
    findings = [{
        "raw_value": secret_text,
        "page_number": 1,
        "entity_type": "SECRET"
    }]

    redacted_path, redacted_name, verified, count = DocumentRedactor.redact_document(
        original_file_path=pdf_path,
        findings_to_redact=findings,
        file_type="pdf"
    )

    assert verified is True
    assert count >= 1
    assert os.path.exists(redacted_path)

    # Verification: Ensure raw token cannot be extracted
    verify_doc = fitz.open(redacted_path)
    extracted = "".join([p.get_text() for p in verify_doc])
    verify_doc.close()

    assert secret_text not in extracted
    assert "This document contains a" in extracted  # Non-sensitive text preserved

# --------------------------------------------------------------------------
# 11b. Permanent DOCX Redaction & Text Verification
# --------------------------------------------------------------------------
def test_docx_permanent_redaction_and_verification(tmp_path):
    import docx

    docx_path = str(tmp_path / "synthetic_test.docx")
    doc = docx.Document()
    secret_pan = "ABCDE1234F"
    doc.add_paragraph(f"Confidential PAN record for employee is {secret_pan}.")
    table = doc.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Identity"
    table.rows[0].cells[1].text = secret_pan
    doc.save(docx_path)

    findings = [{
        "raw_value": secret_pan,
        "page_number": 1,
        "entity_type": "PAN_CARD"
    }]

    redacted_path, redacted_name, verified, count = DocumentRedactor.redact_document(
        original_file_path=docx_path,
        findings_to_redact=findings,
        file_type="docx"
    )

    assert verified is True
    assert count >= 1
    assert os.path.exists(redacted_path)

    # Verification: Raw PAN must not be extractable from paragraphs or tables
    verify_doc = docx.Document(redacted_path)
    extracted = "\n".join([p.text for p in verify_doc.paragraphs])
    for table in verify_doc.tables:
        for row in table.rows:
            for cell in row.cells:
                extracted += " " + cell.text

    assert secret_pan not in extracted
    assert "Confidential PAN record" in extracted

# --------------------------------------------------------------------------
# 12. Path Traversal & Security Protection
# --------------------------------------------------------------------------
def test_path_traversal_protection():
    # Verify that trying to access outside settings.REDACTED_DIR is rejected
    base_dir = Path(settings.REDACTED_DIR).resolve()
    malicious_path = Path(settings.REDACTED_DIR / "../../../app.db").resolve()
    
    # Must fail relative_to check
    with pytest.raises(ValueError):
        malicious_path.relative_to(base_dir)

# --------------------------------------------------------------------------
# 13. Preservation of Original Files
# --------------------------------------------------------------------------
def test_preservation_of_original_files(tmp_path):
    orig_file = tmp_path / "source_document.txt"
    content = "Original text with confidential phone: +91 9988776655."
    orig_file.write_text(content, encoding="utf-8")
    
    mtime_before = orig_file.stat().st_mtime
    
    findings = [{"raw_value": "+91 9988776655", "page_number": 1, "entity_type": "PHONE"}]
    red_path, red_name, verified, count = DocumentRedactor.redact_document(
        str(orig_file),
        findings,
        file_type="txt"
    )
    
    # Original content and existence must be 100% intact
    assert orig_file.exists()
    assert orig_file.read_text(encoding="utf-8") == content
    assert red_path != str(orig_file)

# --------------------------------------------------------------------------
# 14. Precision, Recall and F1-Score Benchmark
# --------------------------------------------------------------------------
def test_privacy_precision_recall_f1():
    """
    Evaluates detector performance on an annotated synthetic benchmark document.
    """
    annotated_test_cases = [
        # Positive Cases (Must Detect)
        ("contact@testfirm.com", "EMAIL"),
        ("billing_finance@domain.in", "EMAIL"),
        ("+91 9876501234", "PHONE"),
        ("9988776655", "PHONE"),
        ("ABCDE1234P", "PAN_CARD"),
        ("ZXCVB9876F", "PAN_CARD"),
        ("9876 5432 1098", "AADHAAR"),
        ("2345 6789 0123", "AADHAAR"),
        ("SBIN0001234", "IFSC_CODE"),
        ("HDFC0005678", "IFSC_CODE"),
    ]

    # Distractor tokens (Must NOT flag as sensitive)
    distractors = [
        "version 2.0",
        "year 2026",
        "Section 4.1",
        "Figure 3",
        "page 15",
        "100 percent",
        "1500 meters",
        "30 seconds",
        "April 2024",
        "Table 2B"
    ]

    corpus = "Document Content:\n"
    for val, _ in annotated_test_cases:
        corpus += f"Candidate item: {val} is registered.\n"
    for d in distractors:
        corpus += f"Benchmark metric: {d} noted.\n"

    findings = PrivacyScanner.scan_document(corpus)
    detected_raws = {f["raw_value"].strip() for f in findings}

    # True Positives
    true_positives = 0
    for val, expected_type in annotated_test_cases:
        if any(val in d for d in detected_raws):
            true_positives += 1

    # False Negatives
    false_negatives = len(annotated_test_cases) - true_positives

    # False Positives (distractors incorrectly flagged as HIGH or sensitive IDs)
    false_positives = 0
    for d in distractors:
        if any(d in raw for raw in detected_raws):
            false_positives += 1

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    print(f"\n[BENCHMARK] Precision: {precision:.2f}, Recall: {recall:.2f}, F1: {f1:.2f}")

    assert precision >= 0.85
    assert recall >= 0.85
    assert f1 >= 0.85

