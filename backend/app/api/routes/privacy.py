import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db import repository
from app.services.privacy_scanner import PrivacyScanner
from app.services.document_redactor import DocumentRedactor
from app.services.extractor import DocumentExtractor

router = APIRouter(tags=["privacy"])

# Request / Response Schemas
class FindingStatusUpdate(BaseModel):
    review_status: str  # confirmed_sensitive, not_sensitive, needs_review

class RedactionRequest(BaseModel):
    finding_ids: List[int]
    redaction_label: Optional[str] = "REDACTED"

class PrivacyFindingItem(BaseModel):
    id: int
    entity_type: str
    masked_value: str
    risk_level: str
    detection_method: str
    confidence: float
    page_number: int
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    explanation: Optional[str] = None
    review_status: str
    is_redacted: bool

class RiskSummaryModel(BaseModel):
    high: int
    medium: int
    low: int
    overall_risk: str

class PrivacyReportResponse(BaseModel):
    document_id: str
    filename: str
    total_findings: int
    risk_summary: RiskSummaryModel
    category_distribution: Dict[str, int]
    page_distribution: Dict[str, int]
    recommended_actions: List[str]
    findings: List[PrivacyFindingItem]

@router.get("/documents/{doc_id}/privacy", response_model=PrivacyReportResponse)
def get_document_privacy_report(doc_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the sensitive information privacy report for a specific document.
    Automatically generates initial findings for existing documents if not yet scanned.
    """
    doc = repository.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    findings = repository.get_privacy_findings(db, doc_id)

    # If document is completed but never scanned, run an automated scan
    if not findings and doc.status == "completed" and doc.extracted_text:
        pages = []
        if doc.file_path and os.path.exists(doc.file_path):
            try:
                extraction = DocumentExtractor.extract(doc.file_path)
                pages = extraction.get("pages", [])
            except Exception:
                pass
        
        scanned_findings = PrivacyScanner.scan_document(doc.extracted_text, pages=pages)
        repository.save_privacy_findings(db, doc_id, scanned_findings)
        findings = repository.get_privacy_findings(db, doc_id)

    findings_data = [
        {
            "id": f.id,
            "entity_type": f.entity_type,
            "raw_value": f.raw_value,
            "masked_value": f.masked_value,
            "risk_level": f.risk_level,
            "detection_method": f.detection_method,
            "confidence": f.confidence,
            "page_number": f.page_number,
            "start_char": f.start_char,
            "end_char": f.end_char,
            "explanation": f.explanation,
            "review_status": f.review_status,
            "is_redacted": f.is_redacted
        }
        for f in findings
    ]

    report = PrivacyScanner.generate_privacy_report(
        findings=findings_data,
        document_id=doc.id,
        filename=doc.filename
    )

    # Format page distribution keys as strings for Pydantic
    page_dist = {str(k): v for k, v in report.get("page_distribution", {}).items()}

    return {
        "document_id": doc.id,
        "filename": doc.filename,
        "total_findings": report["total_findings"],
        "risk_summary": report["risk_summary"],
        "category_distribution": report["category_distribution"],
        "page_distribution": page_dist,
        "recommended_actions": report["recommended_actions"],
        "findings": [
            {
                "id": f["id"],
                "entity_type": f["entity_type"],
                "masked_value": f["masked_value"],
                "risk_level": f["risk_level"],
                "detection_method": f["detection_method"],
                "confidence": f["confidence"],
                "page_number": f["page_number"],
                "start_char": f["start_char"],
                "end_char": f["end_char"],
                "explanation": f["explanation"],
                "review_status": f["review_status"],
                "is_redacted": f["is_redacted"]
            }
            for f in findings_data
        ]
    }

@router.post("/documents/{doc_id}/privacy/scan", response_model=PrivacyReportResponse)
def run_document_privacy_scan(doc_id: str, db: Session = Depends(get_db)):
    """
    Triggers or re-runs a full privacy scan on a document.
    """
    doc = repository.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if not doc.extracted_text:
        raise HTTPException(status_code=400, detail="Document text has not been extracted yet.")

    pages = []
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            extraction = DocumentExtractor.extract(doc.file_path)
            pages = extraction.get("pages", [])
        except Exception:
            pass

    scanned_findings = PrivacyScanner.scan_document(doc.extracted_text, pages=pages)
    repository.save_privacy_findings(db, doc_id, scanned_findings)
    return get_document_privacy_report(doc_id, db)

@router.patch("/privacy/findings/{finding_id}")
def update_finding_review_status(
    finding_id: int,
    req: FindingStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Updates the review status for a specific finding (confirmed_sensitive, not_sensitive, needs_review).
    """
    allowed_statuses = {"confirmed_sensitive", "not_sensitive", "needs_review"}
    if req.review_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{req.review_status}'. Allowed: {', '.join(allowed_statuses)}"
        )

    updated = repository.update_privacy_finding_status(db, finding_id, req.review_status)
    if not updated:
        raise HTTPException(status_code=404, detail="Finding not found.")

    return {
        "id": updated.id,
        "document_id": updated.document_id,
        "review_status": updated.review_status,
        "entity_type": updated.entity_type,
        "masked_value": updated.masked_value
    }

@router.post("/documents/{doc_id}/privacy/redact")
def redact_document_findings(
    doc_id: str,
    req: RedactionRequest,
    db: Session = Depends(get_db)
):
    """
    Applies permanent byte-level redaction on user-selected sensitive findings.
    Preserves original file, creates a separate verified sanitized copy, and returns download details.
    """
    doc = repository.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Original source file not found on server.")

    if not req.finding_ids:
        raise HTTPException(status_code=400, detail="Please select at least one finding to redact.")

    # Fetch findings to redact
    all_findings = repository.get_privacy_findings(db, doc_id)
    selected_findings = [f for f in all_findings if f.id in req.finding_ids]

    if not selected_findings:
        raise HTTPException(status_code=400, detail="None of the specified finding IDs belong to this document.")

    findings_data = [
        {
            "id": f.id,
            "raw_value": f.raw_value,
            "page_number": f.page_number,
            "entity_type": f.entity_type
        }
        for f in selected_findings
    ]

    try:
        redacted_path, redacted_filename, verified, applied_count = DocumentRedactor.redact_document(
            original_file_path=doc.file_path,
            findings_to_redact=findings_data,
            file_type=doc.file_type,
            redaction_label=req.redaction_label or "REDACTED"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redaction process failed: {str(e)}")

    if not verified:
        raise HTTPException(
            status_code=500,
            detail="Redaction verification failed! Sensitive content could still be extracted from the output file."
        )

    # Create redaction history record
    record = repository.create_redaction_record(
        db=db,
        doc_id=doc_id,
        original_filename=doc.filename,
        redacted_filename=redacted_filename,
        redacted_file_path=redacted_path,
        file_type=doc.file_type,
        findings_count=len(selected_findings),
        verified=verified
    )

    # Mark findings as redacted in DB
    repository.mark_findings_redacted(db, req.finding_ids)

    return {
        "status": "success",
        "redaction_id": record.id,
        "document_id": doc_id,
        "original_filename": doc.filename,
        "redacted_filename": record.redacted_filename,
        "findings_count": len(selected_findings),
        "verified": record.verified,
        "download_url": f"/api/privacy/download/{record.id}",
        "created_at": record.created_at.isoformat() if record.created_at else None
    }

@router.get("/documents/{doc_id}/privacy/redacted")
def get_document_redaction_history(doc_id: str, db: Session = Depends(get_db)):
    """
    Returns the list of previously generated redacted files for a document.
    """
    doc = repository.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    redactions = repository.get_document_redactions(db, doc_id)
    return [
        {
            "id": r.id,
            "original_filename": r.original_filename,
            "redacted_filename": r.redacted_filename,
            "file_type": r.file_type,
            "findings_count": r.findings_count,
            "verified": r.verified,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "download_url": f"/api/privacy/download/{r.id}"
        }
        for r in redactions
    ]

@router.get("/privacy/download/{redaction_id}")
def download_redacted_document(redaction_id: str, db: Session = Depends(get_db)):
    """
    Securely serves the verified redacted document for user download with path traversal protection.
    """
    redaction = repository.get_redaction_record(db, redaction_id)
    if not redaction:
        raise HTTPException(status_code=404, detail="Redaction record not found.")

    file_path = Path(redaction.redacted_file_path).resolve()
    redacted_base_dir = Path(settings.REDACTED_DIR).resolve()

    # Path traversal protection: ensure file is inside settings.REDACTED_DIR
    try:
        file_path.relative_to(redacted_base_dir)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied: Invalid file path.")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Redacted file not found on server storage.")

    media_type = "application/pdf" if redaction.file_type == "pdf" else "application/octet-stream"
    return FileResponse(
        path=str(file_path),
        filename=redaction.redacted_filename,
        media_type=media_type
    )

