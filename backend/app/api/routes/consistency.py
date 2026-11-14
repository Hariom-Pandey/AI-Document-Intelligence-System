import uuid
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import repository
from app.services.extractor import DocumentExtractor
from app.services.conflict_reporter import ConflictReporter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/intelligence", tags=["Consistency & Contradiction Intelligence"])

# -------------------------------------------------------------
# Request & Response Schemas
# -------------------------------------------------------------
class AnalyzeConsistencyRequest(BaseModel):
    document_ids: List[str] = Field(..., min_length=2, description="List of document IDs to analyze")
    min_similarity: Optional[float] = Field(None, ge=0.1, le=1.0)
    scope: Optional[str] = Field("selected", description="'selected' or 'collection'")

class DirectCompareRequest(BaseModel):
    document_a_id: str
    document_b_id: str
    min_similarity: Optional[float] = None

class UpdateConflictStatusRequest(BaseModel):
    review_status: str = Field(..., description="confirmed_conflict, valid_revision, false_positive, needs_review, resolved")

# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------
@router.post("/consistency/analyze")
def start_consistency_analysis(
    req: AnalyzeConsistencyRequest,
    db: Session = Depends(get_db)
):
    """
    Initiates cross-document contradiction and consistency detection across selected documents.
    """
    # 1. Validate that all requested documents exist
    documents_data = []
    for doc_id in req.document_ids:
        doc = repository.get_document(db, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")
        if not doc.extracted_text:
            raise HTTPException(
                status_code=400,
                detail=f"Document '{doc.filename}' ({doc_id}) text has not been extracted yet."
            )

        # Retrieve pages if available
        pages = []
        if doc.file_path:
            try:
                extraction = DocumentExtractor.extract(doc.file_path)
                pages = extraction.get("pages", [])
            except Exception:
                pages = []

        documents_data.append({
            "id": doc.id,
            "filename": doc.filename,
            "extracted_text": doc.extracted_text,
            "pages": pages
        })

    # 2. Create consistency analysis job in database
    analysis_id = str(uuid.uuid4())
    job = repository.create_consistency_job(
        db=db,
        analysis_id=analysis_id,
        document_ids=req.document_ids
    )

    try:
        # 3. Run analysis
        repository.update_consistency_job(db, analysis_id, status="processing")
        
        report = ConflictReporter.generate_consistency_report(
            documents_data,
            min_similarity=req.min_similarity
        )

        # 4. Save conflicts to database
        conflicts_to_save = []
        for finding in report["findings"]:
            conflicts_to_save.append({
                "document_a_id": finding["document_a_id"],
                "document_b_id": finding["document_b_id"],
                "statement_a": finding["statement_a"],
                "statement_b": finding["statement_b"],
                "page_a": finding.get("page_a", 1),
                "page_b": finding.get("page_b", 1),
                "conflict_type": finding["conflict_type"],
                "nli_label": finding.get("nli_label", "CONTRADICTION"),
                "confidence": finding.get("confidence", 0.0),
                "explanation": finding.get("explanation", ""),
                "evidence_context": finding.get("evidence_context", {}),
                "review_status": finding.get("review_status", "needs_review")
            })

        repository.save_document_conflicts(db, analysis_id, conflicts_to_save)

        # 5. Mark job completed
        repository.update_consistency_job(
            db,
            analysis_id,
            status="completed",
            total_pairs=report["total_pairs_analyzed"],
            processed_pairs=report["total_pairs_analyzed"],
            conflict_count=report["total_conflicts"],
            categories_summary=report["categories_distribution"]
        )

        return {
            "status": "completed",
            "analysis_id": analysis_id,
            "document_ids": req.document_ids,
            "total_pairs": report["total_pairs_analyzed"],
            "conflict_count": report["total_conflicts"],
            "categories_summary": report["categories_distribution"],
            "report": report
        }

    except Exception as e:
        logger.error(f"Consistency analysis failed: {e}", exc_info=True)
        repository.update_consistency_job(db, analysis_id, status="failed", error_message=str(e))
        raise HTTPException(status_code=500, detail=f"Consistency analysis failed: {str(e)}")


@router.get("/consistency/{analysis_id}")
def get_consistency_analysis_status(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns the execution status and findings of a consistency analysis job.
    """
    job = repository.get_consistency_job(db, analysis_id)
    if not job:
        raise HTTPException(status_code=404, detail="Consistency analysis job not found.")

    conflicts = repository.get_document_conflicts(db, analysis_id=analysis_id)

    # Hydrate document metadata
    doc_map = {}
    for doc_id in (job.document_ids or []):
        doc = repository.get_document(db, doc_id)
        if doc:
            doc_map[doc.id] = doc.filename

    findings_list = []
    for c in conflicts:
        findings_list.append({
            "id": c.id,
            "analysis_id": c.analysis_id,
            "document_a_id": c.document_a_id,
            "document_a_name": doc_map.get(c.document_a_id, "Document A"),
            "document_b_id": c.document_b_id,
            "document_b_name": doc_map.get(c.document_b_id, "Document B"),
            "statement_a": c.statement_a,
            "statement_b": c.statement_b,
            "page_a": c.page_a,
            "page_b": c.page_b,
            "conflict_type": c.conflict_type,
            "nli_label": c.nli_label,
            "confidence": c.confidence,
            "explanation": c.explanation,
            "evidence_context": c.evidence_context or {},
            "review_status": c.review_status,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })

    return {
        "analysis_id": job.analysis_id,
        "status": job.status,
        "document_ids": job.document_ids,
        "total_pairs": job.total_pairs,
        "processed_pairs": job.processed_pairs,
        "conflict_count": job.conflict_count,
        "categories_summary": job.categories_summary or {},
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "findings": findings_list
    }


@router.get("/conflicts")
def list_conflicts(
    analysis_id: Optional[str] = Query(None),
    document_id: Optional[str] = Query(None),
    conflict_type: Optional[str] = Query(None),
    review_status: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns stored conflict findings filtered by document, category, confidence, or review status.
    """
    conflicts = repository.get_document_conflicts(
        db=db,
        analysis_id=analysis_id,
        document_id=document_id,
        conflict_type=conflict_type,
        review_status=review_status,
        min_confidence=min_confidence
    )

    # Cache doc names to avoid duplicate queries
    doc_cache = {}
    def get_name(did):
        if did not in doc_cache:
            d = repository.get_document(db, did)
            doc_cache[did] = d.filename if d else "Document"
        return doc_cache[did]

    return [
        {
            "id": c.id,
            "analysis_id": c.analysis_id,
            "document_a_id": c.document_a_id,
            "document_a_name": get_name(c.document_a_id),
            "document_b_id": c.document_b_id,
            "document_b_name": get_name(c.document_b_id),
            "statement_a": c.statement_a,
            "statement_b": c.statement_b,
            "page_a": c.page_a,
            "page_b": c.page_b,
            "conflict_type": c.conflict_type,
            "nli_label": c.nli_label,
            "confidence": c.confidence,
            "explanation": c.explanation,
            "evidence_context": c.evidence_context or {},
            "review_status": c.review_status,
            "created_at": c.created_at.isoformat() if c.created_at else None
        }
        for c in conflicts
    ]


@router.get("/conflicts/{conflict_id}")
def get_conflict_detail(
    conflict_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieves full details and evidence context for a specific conflict finding.
    """
    c = repository.get_document_conflict(db, conflict_id)
    if not c:
        raise HTTPException(status_code=404, detail="Conflict record not found.")

    doc_a = repository.get_document(db, c.document_a_id)
    doc_b = repository.get_document(db, c.document_b_id)

    return {
        "id": c.id,
        "analysis_id": c.analysis_id,
        "document_a_id": c.document_a_id,
        "document_a_name": doc_a.filename if doc_a else "Document A",
        "document_b_id": c.document_b_id,
        "document_b_name": doc_b.filename if doc_b else "Document B",
        "statement_a": c.statement_a,
        "statement_b": c.statement_b,
        "page_a": c.page_a,
        "page_b": c.page_b,
        "conflict_type": c.conflict_type,
        "nli_label": c.nli_label,
        "confidence": c.confidence,
        "explanation": c.explanation,
        "evidence_context": c.evidence_context or {},
        "review_status": c.review_status,
        "created_at": c.created_at.isoformat() if c.created_at else None
    }


@router.patch("/conflicts/{conflict_id}")
def update_conflict_status(
    conflict_id: int,
    req: UpdateConflictStatusRequest,
    db: Session = Depends(get_db)
):
    """
    Updates the review status of a conflict finding
    (confirmed_conflict, valid_revision, false_positive, needs_review, resolved).
    """
    valid_statuses = {"confirmed_conflict", "valid_revision", "false_positive", "needs_review", "resolved"}
    if req.review_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid review_status. Allowed values: {', '.join(sorted(valid_statuses))}"
        )

    updated = repository.update_conflict_status(db, conflict_id, req.review_status)
    if not updated:
        raise HTTPException(status_code=404, detail="Conflict finding not found.")

    return {
        "id": updated.id,
        "conflict_type": updated.conflict_type,
        "review_status": updated.review_status,
        "updated_at": updated.created_at.isoformat() if updated.created_at else None
    }


@router.post("/consistency/compare")
def compare_document_pair_direct(
    req: DirectCompareRequest,
    db: Session = Depends(get_db)
):
    """
    Directly compares two documents and returns detailed side-by-side consistency findings.
    """
    doc_a = repository.get_document(db, req.document_a_id)
    doc_b = repository.get_document(db, req.document_b_id)

    if not doc_a:
        raise HTTPException(status_code=404, detail=f"Document A '{req.document_a_id}' not found.")
    if not doc_b:
        raise HTTPException(status_code=404, detail=f"Document B '{req.document_b_id}' not found.")

    if not doc_a.extracted_text or not doc_b.extracted_text:
        raise HTTPException(status_code=400, detail="One or both documents have not been processed yet.")

    pages_a = []
    pages_b = []
    if doc_a.file_path:
        try:
            pages_a = DocumentExtractor.extract(doc_a.file_path).get("pages", [])
        except Exception:
            pages_a = []
    if doc_b.file_path:
        try:
            pages_b = DocumentExtractor.extract(doc_b.file_path).get("pages", [])
        except Exception:
            pages_b = []

    doc_a_dict = {
        "id": doc_a.id,
        "filename": doc_a.filename,
        "extracted_text": doc_a.extracted_text,
        "pages": pages_a
    }
    doc_b_dict = {
        "id": doc_b.id,
        "filename": doc_b.filename,
        "extracted_text": doc_b.extracted_text,
        "pages": pages_b
    }

    report = ConflictReporter.analyze_document_pair(
        doc_a_dict,
        doc_b_dict,
        min_similarity=req.min_similarity
    )

    return report

