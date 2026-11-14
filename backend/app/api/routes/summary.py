from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.db.database import get_db
from app.db import repository
from app.services.summarizer import DocumentSummarizer

router = APIRouter(prefix="/documents", tags=["summary"])

class SummaryResponse(BaseModel):
    document_id: str
    short_summary: str
    detailed_summary: str
    key_points: List[str]

@router.post("/{doc_id}/summarize", response_model=SummaryResponse)
def summarize_document(doc_id: str, db: Session = Depends(get_db)):
    """
    Generate or regenerate the document summary and key points.
    """
    doc = repository.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if not doc.extracted_text:
        raise HTTPException(status_code=400, detail="Document has no extracted text to summarize.")

    try:
        summary_result = DocumentSummarizer.summarize(doc.extracted_text)
        summary = repository.save_summary(
            db,
            doc_id=doc_id,
            short_summary=summary_result["short_summary"],
            detailed_summary=summary_result["detailed_summary"],
            key_points=summary_result["key_points"]
        )

        return {
            "document_id": doc_id,
            "short_summary": summary.short_summary,
            "detailed_summary": summary.detailed_summary,
            "key_points": summary.key_points or []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")

