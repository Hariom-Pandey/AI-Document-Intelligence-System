from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.db.database import get_db
from app.db import repository
from app.services.qa_service import QAService

router = APIRouter(tags=["chat"])

class QuestionRequest(BaseModel):
    question: str
    top_k: Optional[int] = 4

class CitationModel(BaseModel):
    document_id: Optional[str]
    page_number: int
    chunk_index: int
    score: float
    snippet: str

class AnswerResponse(BaseModel):
    question: str
    answer: str
    has_evidence: bool
    citations: List[CitationModel]
    document_id: Optional[str] = None

@router.post("/documents/{doc_id}/ask", response_model=AnswerResponse)
def ask_document_question(
    doc_id: str,
    req: QuestionRequest,
    db: Session = Depends(get_db)
):
    """
    RAG endpoint to ask questions about a specific document.
    Retrieves top relevant chunks, passes them to the QA model, and returns evidence citations.
    """
    doc = repository.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Document is not ready for chat (current status: {doc.status})."
        )

    result = QAService.answer_question(
        question=req.question,
        document_id=doc_id,
        top_k=req.top_k or 4
    )

    # Persist question & answer in database
    repository.save_query(
        db,
        doc_id=doc_id,
        question=req.question,
        answer=result["answer"],
        citations=result["citations"]
    )

    return {
        "question": req.question,
        "answer": result["answer"],
        "has_evidence": result["has_evidence"],
        "citations": result["citations"],
        "document_id": doc_id
    }

@router.get("/documents/{doc_id}/history")
def get_chat_history(doc_id: str, db: Session = Depends(get_db)):
    """
    Retrieve previous chat interactions and citations for a document.
    """
    queries = repository.get_document_queries(db, doc_id=doc_id)
    return [
        {
            "id": q.id,
            "question": q.question,
            "answer": q.answer,
            "citations": q.citations,
            "created_at": q.created_at.isoformat() if q.created_at else None
        }
        for q in queries
    ]

@router.delete("/documents/{doc_id}/history")
def clear_chat_history(doc_id: str, db: Session = Depends(get_db)):
    """
    Clear chat history for a specific document.
    """
    count = repository.clear_document_queries(db, doc_id=doc_id)
    return {"status": "success", "cleared_count": count}

@router.post("/chat", response_model=AnswerResponse)
def cross_document_chat(
    req: QuestionRequest,
    document_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    General semantic Q&A endpoint across all documents or an optional target document.
    """
    result = QAService.answer_question(
        question=req.question,
        document_id=document_id,
        top_k=req.top_k or 4
    )

    repository.save_query(
        db,
        doc_id=document_id,
        question=req.question,
        answer=result["answer"],
        citations=result["citations"]
    )

    return {
        "question": req.question,
        "answer": result["answer"],
        "has_evidence": result["has_evidence"],
        "citations": result["citations"],
        "document_id": document_id
    }

