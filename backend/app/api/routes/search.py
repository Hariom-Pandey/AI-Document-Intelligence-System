from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.db.database import get_db
from app.db import repository
from app.services.retriever import DocumentRetriever

router = APIRouter(prefix="/search", tags=["search"])

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 6
    document_id: Optional[str] = None
    min_score: Optional[float] = 0.20

class SearchResultItem(BaseModel):
    document_id: str
    filename: Optional[str] = "Unknown"
    category: Optional[str] = "Uncategorized"
    page_number: int
    chunk_index: int
    score: float
    snippet: str

class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultItem]

@router.post("", response_model=SearchResponse)
def semantic_search(req: SearchRequest, db: Session = Depends(get_db)):
    """
    Semantic search across indexed document passages by meaning using dense embeddings.
    """
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")

    raw_results = DocumentRetriever.retrieve(
        query=req.query,
        document_id=req.document_id,
        top_k=req.top_k or 6,
        min_score=req.min_score or 0.20
    )

    # Attach document metadata (filename, category) for display
    enriched_results = []
    doc_cache = {}

    for item in raw_results:
        doc_id = item.get("document_id")
        if doc_id not in doc_cache:
            doc = repository.get_document(db, doc_id) if doc_id else None
            doc_cache[doc_id] = {
                "filename": doc.filename if doc else "Deleted Document",
                "category": doc.classification.category if doc and doc.classification else "General"
            }

        meta = doc_cache[doc_id]
        enriched_results.append({
            "document_id": doc_id or "",
            "filename": meta["filename"],
            "category": meta["category"],
            "page_number": item.get("page_number", 1),
            "chunk_index": item.get("chunk_index", 0),
            "score": round(float(item.get("score", 0.0)), 4),
            "snippet": item.get("text", "")
        })

    return {
        "query": req.query,
        "total_results": len(enriched_results),
        "results": enriched_results
    }

