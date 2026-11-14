from __future__ import annotations

from typing import Literal
from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: int
    filename: str
    file_type: str
    category: str
    processing_status: str
    created_at: str


class SummaryResponse(BaseModel):
    document_id: int
    category: str
    summary: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class QuestionRequest(BaseModel):
    question: str
    top_k: int = 4


class FindingStatusUpdate(BaseModel):
    review_status: Literal["Confirmed Sensitive", "Not Sensitive", "Needs Review"]
    selected_for_redaction: bool | None = None


class ComparisonRequest(BaseModel):
    document_ids: list[int]
    max_pairs: int = 40
