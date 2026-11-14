from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import (
    Document,
    DocumentSummary,
    DocumentEntity,
    DocumentClassification,
    DocumentChunk,
    DocumentQuery,
    DocumentPrivacyFinding,
    DocumentRedaction,
    ConsistencyAnalysisJob,
    DocumentConflict
)

def create_document(
    db: Session,
    filename: str,
    file_path: str,
    file_type: str,
    file_size: int = 0,
    doc_id: Optional[str] = None
) -> Document:
    doc = Document(
        id=doc_id,
        filename=filename,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        status="uploaded"
    )
    if doc_id:
        doc.id = doc_id
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def get_document(db: Session, doc_id: str) -> Optional[Document]:
    return db.query(Document).filter(Document.id == doc_id).first()

def get_documents(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
) -> List[Document]:
    query = db.query(Document)
    if status:
        query = query.filter(Document.status == status)
    return query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

def update_document_status(
    db: Session,
    doc_id: str,
    status: str,
    error_message: Optional[str] = None,
    page_count: Optional[int] = None,
    extracted_text: Optional[str] = None
) -> Optional[Document]:
    doc = get_document(db, doc_id)
    if not doc:
        return None
    doc.status = status
    if error_message is not None:
        doc.error_message = error_message
    elif status == "completed":
        doc.error_message = None
    if page_count is not None:
        doc.page_count = page_count
    if extracted_text is not None:
        doc.extracted_text = extracted_text
    db.commit()
    db.refresh(doc)
    return doc

def delete_document(db: Session, doc_id: str) -> bool:
    doc = get_document(db, doc_id)
    if not doc:
        return False
    db.delete(doc)
    db.commit()
    return True

def save_summary(
    db: Session,
    doc_id: str,
    short_summary: str,
    detailed_summary: str,
    key_points: Optional[List[str]] = None
) -> DocumentSummary:
    existing = db.query(DocumentSummary).filter(DocumentSummary.document_id == doc_id).first()
    if existing:
        existing.short_summary = short_summary
        existing.detailed_summary = detailed_summary
        existing.key_points = key_points or []
        db.commit()
        db.refresh(existing)
        return existing
    summary = DocumentSummary(
        document_id=doc_id,
        short_summary=short_summary,
        detailed_summary=detailed_summary,
        key_points=key_points or []
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary

def save_entities(db: Session, doc_id: str, entities_data: List[Dict[str, Any]]) -> List[DocumentEntity]:
    # Remove existing entities for document
    db.query(DocumentEntity).filter(DocumentEntity.document_id == doc_id).delete()
    entities = []
    for item in entities_data:
        ent = DocumentEntity(
            document_id=doc_id,
            text=item.get("text", ""),
            label=item.get("label", ""),
            start_char=item.get("start_char"),
            end_char=item.get("end_char"),
            page_number=item.get("page_number", 1)
        )
        entities.append(ent)
        db.add(ent)
    db.commit()
    return entities

def save_classification(
    db: Session,
    doc_id: str,
    category: str,
    confidence: float,
    all_scores: Optional[Dict[str, float]] = None
) -> DocumentClassification:
    existing = db.query(DocumentClassification).filter(DocumentClassification.document_id == doc_id).first()
    if existing:
        existing.category = category
        existing.confidence = confidence
        existing.all_scores = all_scores or {}
        db.commit()
        db.refresh(existing)
        return existing
    clf = DocumentClassification(
        document_id=doc_id,
        category=category,
        confidence=confidence,
        all_scores=all_scores or {}
    )
    db.add(clf)
    db.commit()
    db.refresh(clf)
    return clf

def save_chunks(db: Session, doc_id: str, chunks_data: List[Dict[str, Any]]) -> List[DocumentChunk]:
    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete()
    chunks = []
    for item in chunks_data:
        c = DocumentChunk(
            document_id=doc_id,
            chunk_index=item.get("chunk_index", 0),
            page_number=item.get("page_number", 1),
            text=item.get("text", ""),
            token_count=item.get("token_count", 0)
        )
        chunks.append(c)
        db.add(c)
    db.commit()
    return chunks

def get_document_chunks(db: Session, doc_id: str) -> List[DocumentChunk]:
    return db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).order_by(DocumentChunk.chunk_index.asc()).all()

def get_all_chunks(db: Session) -> List[DocumentChunk]:
    return db.query(DocumentChunk).all()

def save_query(
    db: Session,
    doc_id: Optional[str],
    question: str,
    answer: str,
    citations: Optional[List[Dict[str, Any]]] = None
) -> DocumentQuery:
    query = DocumentQuery(
        document_id=doc_id,
        question=question,
        answer=answer,
        citations=citations or []
    )
    db.add(query)
    db.commit()
    db.refresh(query)
    return query

def get_document_queries(db: Session, doc_id: Optional[str] = None, limit: int = 50) -> List[DocumentQuery]:
    q = db.query(DocumentQuery)
    if doc_id:
        q = q.filter(DocumentQuery.document_id == doc_id)
    return q.order_by(DocumentQuery.created_at.asc()).limit(limit).all()

def clear_document_queries(db: Session, doc_id: str) -> int:
    deleted = db.query(DocumentQuery).filter(DocumentQuery.document_id == doc_id).delete()
    db.commit()
    return deleted

def get_document_results(db: Session, doc_id: str) -> Optional[Dict[str, Any]]:
    doc = get_document(db, doc_id)
    if not doc:
        return None
    return {
        "document": {
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "page_count": doc.page_count,
            "status": doc.status,
            "error_message": doc.error_message,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
            "extracted_text_preview": (doc.extracted_text[:1000] + "...") if doc.extracted_text and len(doc.extracted_text) > 1000 else doc.extracted_text
        },
        "summary": {
            "short_summary": doc.summary.short_summary if doc.summary else None,
            "detailed_summary": doc.summary.detailed_summary if doc.summary else None,
            "key_points": doc.summary.key_points if doc.summary else []
        } if doc.summary else None,
        "classification": {
            "category": doc.classification.category if doc.classification else None,
            "confidence": doc.classification.confidence if doc.classification else 0.0,
            "all_scores": doc.classification.all_scores if doc.classification else {}
        } if doc.classification else None,
        "entities": [
            {
                "id": ent.id,
                "text": ent.text,
                "label": ent.label,
                "start_char": ent.start_char,
                "end_char": ent.end_char,
                "page_number": ent.page_number
            }
            for ent in doc.entities
        ] if doc.entities else [],
        "chunks_count": len(doc.chunks),
        "privacy": {
            "total_findings": len(doc.privacy_findings),
            "high_risk": sum(1 for f in doc.privacy_findings if f.risk_level == "HIGH"),
            "medium_risk": sum(1 for f in doc.privacy_findings if f.risk_level == "MEDIUM"),
            "low_risk": sum(1 for f in doc.privacy_findings if f.risk_level == "LOW"),
            "redacted_count": sum(1 for f in doc.privacy_findings if f.is_redacted)
        } if doc.privacy_findings else None
    }

def save_privacy_findings(
    db: Session,
    doc_id: str,
    findings_data: List[Dict[str, Any]]
) -> List[DocumentPrivacyFinding]:
    """
    Persists privacy findings for a document. Replaces previous un-redacted findings.
    """
    db.query(DocumentPrivacyFinding).filter(DocumentPrivacyFinding.document_id == doc_id).delete()
    findings = []
    for item in findings_data:
        f = DocumentPrivacyFinding(
            document_id=doc_id,
            entity_type=item.get("entity_type", "UNKNOWN"),
            raw_value=item.get("raw_value", ""),
            masked_value=item.get("masked_value", ""),
            risk_level=item.get("risk_level", "MEDIUM"),
            detection_method=item.get("detection_method", "rule_pattern"),
            confidence=float(item.get("confidence", 1.0)),
            page_number=int(item.get("page_number", 1)),
            start_char=item.get("start_char"),
            end_char=item.get("end_char"),
            explanation=item.get("explanation", ""),
            review_status=item.get("review_status", "needs_review"),
            is_redacted=bool(item.get("is_redacted", False))
        )
        findings.append(f)
    db.add_all(findings)
    db.commit()
    return findings

def get_privacy_findings(
    db: Session,
    doc_id: str,
    review_status: Optional[str] = None
) -> List[DocumentPrivacyFinding]:
    q = db.query(DocumentPrivacyFinding).filter(DocumentPrivacyFinding.document_id == doc_id)
    if review_status:
        q = q.filter(DocumentPrivacyFinding.review_status == review_status)
    return q.order_by(DocumentPrivacyFinding.page_number.asc(), DocumentPrivacyFinding.id.asc()).all()

def get_privacy_finding(db: Session, finding_id: int) -> Optional[DocumentPrivacyFinding]:
    return db.query(DocumentPrivacyFinding).filter(DocumentPrivacyFinding.id == finding_id).first()

def update_privacy_finding_status(
    db: Session,
    finding_id: int,
    review_status: str
) -> Optional[DocumentPrivacyFinding]:
    finding = get_privacy_finding(db, finding_id)
    if not finding:
        return None
    finding.review_status = review_status
    db.commit()
    db.refresh(finding)
    return finding

def mark_findings_redacted(db: Session, finding_ids: List[int]) -> int:
    count = db.query(DocumentPrivacyFinding).filter(
        DocumentPrivacyFinding.id.in_(finding_ids)
    ).update({"is_redacted": True}, synchronize_session=False)
    db.commit()
    return count

def create_redaction_record(
    db: Session,
    doc_id: str,
    original_filename: str,
    redacted_filename: str,
    redacted_file_path: str,
    file_type: str,
    findings_count: int = 0,
    verified: bool = True
) -> DocumentRedaction:
    redaction = DocumentRedaction(
        document_id=doc_id,
        original_filename=original_filename,
        redacted_filename=redacted_filename,
        redacted_file_path=redacted_file_path,
        file_type=file_type,
        findings_count=findings_count,
        verified=verified
    )
    db.add(redaction)
    db.commit()
    db.refresh(redaction)
    return redaction

def get_redaction_record(db: Session, redaction_id: str) -> Optional[DocumentRedaction]:
    return db.query(DocumentRedaction).filter(DocumentRedaction.id == redaction_id).first()

def get_document_redactions(db: Session, doc_id: str) -> List[DocumentRedaction]:
    return db.query(DocumentRedaction).filter(
        DocumentRedaction.document_id == doc_id
    ).order_by(DocumentRedaction.created_at.desc()).all()

def create_consistency_job(
    db: Session,
    analysis_id: str,
    document_ids: List[str]
) -> ConsistencyAnalysisJob:
    job = ConsistencyAnalysisJob(
        analysis_id=analysis_id,
        document_ids=document_ids,
        status="pending",
        total_pairs=0,
        processed_pairs=0,
        conflict_count=0,
        categories_summary={}
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def get_consistency_job(db: Session, analysis_id: str) -> Optional[ConsistencyAnalysisJob]:
    return db.query(ConsistencyAnalysisJob).filter(
        ConsistencyAnalysisJob.analysis_id == analysis_id
    ).first()

def update_consistency_job(
    db: Session,
    analysis_id: str,
    status: Optional[str] = None,
    total_pairs: Optional[int] = None,
    processed_pairs: Optional[int] = None,
    conflict_count: Optional[int] = None,
    categories_summary: Optional[Dict[str, int]] = None,
    error_message: Optional[str] = None
) -> Optional[ConsistencyAnalysisJob]:
    job = get_consistency_job(db, analysis_id)
    if not job:
        return None
    if status is not None:
        job.status = status
        if status in ("completed", "failed"):
            job.completed_at = datetime.utcnow()
    if total_pairs is not None:
        job.total_pairs = total_pairs
    if processed_pairs is not None:
        job.processed_pairs = processed_pairs
    if conflict_count is not None:
        job.conflict_count = conflict_count
    if categories_summary is not None:
        job.categories_summary = categories_summary
    if error_message is not None:
        job.error_message = error_message
    db.commit()
    db.refresh(job)
    return job

def save_document_conflicts(
    db: Session,
    analysis_id: str,
    conflicts_data: List[Dict[str, Any]]
) -> List[DocumentConflict]:
    # Delete existing conflicts for this analysis to prevent duplication
    db.query(DocumentConflict).filter(
        DocumentConflict.analysis_id == analysis_id
    ).delete()
    
    saved = []
    for item in conflicts_data:
        conflict = DocumentConflict(
            analysis_id=analysis_id,
            document_a_id=item["document_a_id"],
            document_b_id=item["document_b_id"],
            statement_a=item["statement_a"],
            statement_b=item["statement_b"],
            page_a=item.get("page_a", 1),
            page_b=item.get("page_b", 1),
            conflict_type=item["conflict_type"],
            nli_label=item.get("nli_label", "CONTRADICTION"),
            confidence=float(item.get("confidence", 0.0)),
            explanation=item.get("explanation", ""),
            evidence_context=item.get("evidence_context", {}),
            review_status=item.get("review_status", "needs_review")
        )
        db.add(conflict)
        saved.append(conflict)
    db.commit()
    for s in saved:
        db.refresh(s)
    return saved

def get_document_conflicts(
    db: Session,
    analysis_id: Optional[str] = None,
    document_id: Optional[str] = None,
    conflict_type: Optional[str] = None,
    review_status: Optional[str] = None,
    min_confidence: Optional[float] = None
) -> List[DocumentConflict]:
    query = db.query(DocumentConflict)
    if analysis_id:
        query = query.filter(DocumentConflict.analysis_id == analysis_id)
    if document_id:
        query = query.filter(
            (DocumentConflict.document_a_id == document_id) |
            (DocumentConflict.document_b_id == document_id)
        )
    if conflict_type:
        query = query.filter(DocumentConflict.conflict_type == conflict_type)
    if review_status:
        query = query.filter(DocumentConflict.review_status == review_status)
    if min_confidence is not None:
        query = query.filter(DocumentConflict.confidence >= min_confidence)
    return query.order_by(DocumentConflict.confidence.desc(), DocumentConflict.created_at.desc()).all()

def get_document_conflict(db: Session, conflict_id: int) -> Optional[DocumentConflict]:
    return db.query(DocumentConflict).filter(DocumentConflict.id == conflict_id).first()

def update_conflict_status(
    db: Session,
    conflict_id: int,
    review_status: str
) -> Optional[DocumentConflict]:
    conflict = get_document_conflict(db, conflict_id)
    if not conflict:
        return None
    conflict.review_status = review_status
    db.commit()
    db.refresh(conflict)
    return conflict

def delete_conflicts_for_analysis(db: Session, analysis_id: str) -> int:
    count = db.query(DocumentConflict).filter(
        DocumentConflict.analysis_id == analysis_id
    ).delete()
    db.commit()
    return count

