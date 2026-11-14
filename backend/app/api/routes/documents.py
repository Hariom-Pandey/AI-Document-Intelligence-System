from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import repository
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document (PDF, DOCX, TXT) and trigger the background NLP pipeline.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing.")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{file_ext}'. Allowed: .pdf, .docx, .txt")

    try:
        doc_id, file_path, file_size = DocumentService.save_uploaded_file(file.filename, file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    doc = repository.create_document(
        db=db,
        filename=file.filename,
        file_path=file_path,
        file_type=file_ext.lstrip("."),
        file_size=file_size,
        doc_id=doc_id
    )

    # Trigger processing pipeline in background
    background_tasks.add_task(DocumentService.process_document_pipeline, db, doc.id)

    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "status": doc.status,
        "message": "Document accepted for processing."
    }

@router.get("")
def list_documents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all documents with their processing status and summary metadata.
    """
    docs = repository.get_documents(db, skip=skip, limit=limit, status=status)
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "file_type": d.file_type,
            "file_size": d.file_size,
            "page_count": d.page_count,
            "status": d.status,
            "error_message": d.error_message,
            "category": d.classification.category if d.classification else None,
            "short_summary": d.summary.short_summary if d.summary else None,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        }
        for d in docs
    ]

@router.get("/{doc_id}")
def get_document_status(doc_id: str, db: Session = Depends(get_db)):
    """
    Get detailed status and metadata of a specific document.
    """
    doc = repository.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "page_count": doc.page_count,
        "status": doc.status,
        "error_message": doc.error_message,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
    }

@router.get("/{doc_id}/results")
def get_document_results(doc_id: str, db: Session = Depends(get_db)):
    """
    Get all extracted intelligence for a document: summary, entities, classification, chunks count.
    """
    results = repository.get_document_results(db, doc_id)
    if not results:
        raise HTTPException(status_code=404, detail="Document not found.")
    return results

@router.post("/{doc_id}/reprocess", status_code=status.HTTP_202_ACCEPTED)
def reprocess_document(
    doc_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Retries or re-runs processing on a document.
    """
    doc = repository.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    background_tasks.add_task(DocumentService.process_document_pipeline, db, doc.id)
    return {"message": "Document re-processing started.", "status": "processing"}

@router.delete("/{doc_id}")
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    """
    Delete a document, its index entries, physical file, and database records.
    """
    success = DocumentService.delete_document_full(db, doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"message": "Document successfully deleted.", "id": doc_id}
