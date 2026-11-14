from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    filepath: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_type: Mapped[str] = mapped_column(String(16), nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="General Business")
    summary: Mapped[str] = mapped_column(Text, default="")
    text_content: Mapped[str] = mapped_column(Text, default="")
    processing_status: Mapped[str] = mapped_column(String(32), default="processed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    chunks: Mapped[list[DocumentChunk]] = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )
    findings: Mapped[list[SensitiveFinding]] = relationship(
        "SensitiveFinding", back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    page_number: Mapped[int] = mapped_column(Integer, default=1)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    vector_json: Mapped[str] = mapped_column(Text, default="[]")

    document: Mapped[Document] = relationship("Document", back_populates="chunks")


class SensitiveFinding(Base):
    __tablename__ = "sensitive_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    value: Mapped[str] = mapped_column(String(512), nullable=False)
    masked_value: Mapped[str] = mapped_column(String(512), nullable=False)
    info_type: Mapped[str] = mapped_column(String(64), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, default=1)
    detection_method: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), default="Low")
    explanation: Mapped[str] = mapped_column(Text, default="")
    review_status: Mapped[str] = mapped_column(String(32), default="Needs Review")
    selected_for_redaction: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float] = mapped_column(Float, default=0.5)

    document: Mapped[Document] = relationship("Document", back_populates="findings")
