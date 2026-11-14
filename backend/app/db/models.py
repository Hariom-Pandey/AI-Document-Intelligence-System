import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Boolean
)
from sqlalchemy.orm import relationship
from app.db.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx, txt
    file_size = Column(Integer, default=0)
    page_count = Column(Integer, default=1)
    status = Column(String(50), default="uploaded", index=True)  # uploaded, processing, completed, failed
    error_message = Column(Text, nullable=True)
    extracted_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    summary = relationship("DocumentSummary", back_populates="document", uselist=False, cascade="all, delete-orphan")
    entities = relationship("DocumentEntity", back_populates="document", cascade="all, delete-orphan")
    classification = relationship("DocumentClassification", back_populates="document", uselist=False, cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    queries = relationship("DocumentQuery", back_populates="document", cascade="all, delete-orphan")
    privacy_findings = relationship("DocumentPrivacyFinding", back_populates="document", cascade="all, delete-orphan")
    redactions = relationship("DocumentRedaction", back_populates="document", cascade="all, delete-orphan")
    conflicts_as_a = relationship("DocumentConflict", foreign_keys="DocumentConflict.document_a_id", back_populates="document_a", cascade="all, delete-orphan")
    conflicts_as_b = relationship("DocumentConflict", foreign_keys="DocumentConflict.document_b_id", back_populates="document_b", cascade="all, delete-orphan")

class DocumentSummary(Base):
    __tablename__ = "document_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True)
    short_summary = Column(Text, nullable=False)
    detailed_summary = Column(Text, nullable=False)
    key_points = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="summary")

class DocumentEntity(Base):
    __tablename__ = "document_entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    text = Column(String(255), nullable=False)
    label = Column(String(50), nullable=False)  # PERSON, ORG, GPE, DATE, etc.
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)
    page_number = Column(Integer, nullable=True)

    document = relationship("Document", back_populates="entities")

class DocumentClassification(Base):
    __tablename__ = "document_classifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True)
    category = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    all_scores = Column(JSON, default=dict)

    document = relationship("Document", back_populates="classification")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, default=1)
    text = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)

    document = relationship("Document", back_populates="chunks")

class DocumentQuery(Base):
    __tablename__ = "document_queries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    citations = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="queries")

class DocumentPrivacyFinding(Base):
    __tablename__ = "document_privacy_findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # PERSON_NAME, EMAIL, PHONE, PAN_CARD, AADHAAR, BANK_ACCOUNT, IFSC_CODE, PASSPORT, ADDRESS, CREDIT_CARD
    raw_value = Column(Text, nullable=False)  # Stored server-side for coordinate search and redaction
    masked_value = Column(String(255), nullable=False)
    risk_level = Column(String(20), nullable=False, default="MEDIUM")  # HIGH, MEDIUM, LOW
    detection_method = Column(String(50), nullable=False)  # regex_pattern_validated, spacy_ner, hybrid_rule
    confidence = Column(Float, nullable=False, default=1.0)
    page_number = Column(Integer, default=1)
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)
    explanation = Column(Text, nullable=True)
    review_status = Column(String(30), default="needs_review", index=True)  # needs_review, confirmed_sensitive, not_sensitive
    is_redacted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="privacy_findings")

class DocumentRedaction(Base):
    __tablename__ = "document_redactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    redacted_filename = Column(String(255), nullable=False)
    redacted_file_path = Column(String(512), nullable=False)
    file_type = Column(String(10), nullable=False)
    findings_count = Column(Integer, default=0)
    verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="redactions")


class ConsistencyAnalysisJob(Base):
    __tablename__ = "consistency_analysis_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(36), unique=True, index=True, nullable=False)
    document_ids = Column(JSON, default=list)  # list of doc_id strings
    status = Column(String(30), default="pending", index=True)  # pending, processing, completed, failed
    total_pairs = Column(Integer, default=0)
    processed_pairs = Column(Integer, default=0)
    conflict_count = Column(Integer, default=0)
    categories_summary = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    conflicts = relationship("DocumentConflict", back_populates="analysis_job", cascade="all, delete-orphan")


class DocumentConflict(Base):
    __tablename__ = "document_conflicts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(36), ForeignKey("consistency_analysis_jobs.analysis_id", ondelete="CASCADE"), nullable=True, index=True)
    document_a_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    document_b_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    statement_a = Column(Text, nullable=False)
    statement_b = Column(Text, nullable=False)
    page_a = Column(Integer, default=1)
    page_b = Column(Integer, default=1)
    conflict_type = Column(String(50), nullable=False, index=True)  # NUMERICAL_INCONSISTENCY, DATE_INCONSISTENCY, FACTUAL_CONTRADICTION, CONTRACTUAL_CONFLICT, RESPONSIBILITY_CONFLICT, ENTITY_INCONSISTENCY, POTENTIAL_VERSION_CHANGE, UNRESOLVED_DIFFERENCE
    nli_label = Column(String(30), nullable=False)  # CONTRADICTION, ENTAILMENT, NEUTRAL
    confidence = Column(Float, nullable=False, default=0.0)
    explanation = Column(Text, nullable=True)
    evidence_context = Column(JSON, default=dict)
    review_status = Column(String(30), default="needs_review", index=True)  # needs_review, confirmed_conflict, valid_revision, false_positive, resolved
    created_at = Column(DateTime, default=datetime.utcnow)

    document_a = relationship("Document", foreign_keys=[document_a_id], back_populates="conflicts_as_a")
    document_b = relationship("Document", foreign_keys=[document_b_id], back_populates="conflicts_as_b")
    analysis_job = relationship("ConsistencyAnalysisJob", foreign_keys=[analysis_id], back_populates="conflicts")



