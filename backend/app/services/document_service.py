import os
import shutil
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import repository
from app.services.extractor import DocumentExtractor
from app.services.preprocessor import TextPreprocessor
from app.services.summarizer import DocumentSummarizer
from app.services.ner import EntityExtractor
from app.services.classifier import DocumentClassifier
from app.services.privacy_scanner import PrivacyScanner
from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)

class DocumentService:
    """
    Coordinates the document processing lifecycle:
    Upload -> Extraction -> Chunking -> NLP Processing -> Indexing -> Persistence.
    """

    @classmethod
    def save_uploaded_file(cls, filename: str, file_bytes: bytes) -> tuple[str, str, int]:
        ext = Path(filename).suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file format '{ext}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}")

        doc_id = str(uuid.uuid4())
        safe_filename = f"{doc_id}_{filename}"
        dest_path = settings.UPLOAD_DIR / safe_filename

        with open(dest_path, "wb") as f:
            f.write(file_bytes)

        file_size = len(file_bytes)
        return doc_id, str(dest_path), file_size

    @classmethod
    def process_document_pipeline(cls, db: Session, doc_id: str):
        """
        Executes end-to-end document intelligence pipeline.
        Can be run synchronously or in a FastAPI background task.
        """
        doc = repository.get_document(db, doc_id)
        if not doc:
            logger.error(f"Document {doc_id} not found in database.")
            return

        logger.info(f"Starting processing for document {doc_id} ({doc.filename})...")
        repository.update_document_status(db, doc_id, status="processing")

        try:
            # 1. Text Extraction
            extraction_result = DocumentExtractor.extract(doc.file_path)
            page_count = extraction_result.get("page_count", 1)
            pages = extraction_result.get("pages", [])
            full_text = extraction_result.get("full_text", "")

            if not full_text or len(full_text.strip()) < 5:
                raise ValueError("No usable text could be extracted from the document.")

            repository.update_document_status(
                db,
                doc_id,
                status="processing",
                page_count=page_count,
                extracted_text=full_text
            )

            # 2. Text Cleaning & Chunking
            chunks = TextPreprocessor.chunk_pages(
                pages=pages,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            repository.save_chunks(db, doc_id, chunks)

            # 3. Summarization
            try:
                summary_data = DocumentSummarizer.summarize(full_text)
                repository.save_summary(
                    db,
                    doc_id=doc_id,
                    short_summary=summary_data["short_summary"],
                    detailed_summary=summary_data["detailed_summary"],
                    key_points=summary_data["key_points"]
                )
            except Exception as e:
                logger.error(f"Summarization error for document {doc_id}: {e}")
                repository.save_summary(
                    db,
                    doc_id=doc_id,
                    short_summary="Summary generation encountered an error.",
                    detailed_summary=str(e),
                    key_points=[]
                )

            # 4. Entity Extraction (NER)
            try:
                entities_data = EntityExtractor.extract_entities(full_text, pages=pages)
                repository.save_entities(db, doc_id, entities_data)
            except Exception as e:
                logger.error(f"NER extraction error for document {doc_id}: {e}")

            # 5. Document Classification
            try:
                clf_result = DocumentClassifier.classify(full_text)
                repository.save_classification(
                    db,
                    doc_id=doc_id,
                    category=clf_result["category"],
                    confidence=clf_result["confidence"],
                    all_scores=clf_result["all_scores"]
                )
            except Exception as e:
                logger.error(f"Classification error for document {doc_id}: {e}")
                repository.save_classification(
                    db,
                    doc_id=doc_id,
                    category="Unclassified",
                    confidence=0.0,
                    all_scores={}
                )

            # 6. FAISS Vector Indexing
            try:
                vector_store.add_document_chunks(doc_id, chunks)
            except Exception as e:
                logger.error(f"Vector indexing error for document {doc_id}: {e}")
                raise RuntimeError(f"Embedding and vector indexing failed: {e}")

            # 7. Privacy & Sensitive Information Scan
            try:
                privacy_findings = PrivacyScanner.scan_document(full_text, pages=pages)
                repository.save_privacy_findings(db, doc_id, privacy_findings)
                logger.info(f"Privacy scan identified {len(privacy_findings)} findings for document {doc_id}.")
            except Exception as e:
                logger.error(f"Privacy scanning error for document {doc_id}: {e}")

            # 8. Mark Completed
            repository.update_document_status(db, doc_id, status="completed", error_message=None)
            logger.info(f"Document {doc_id} processed successfully.")

        except Exception as e:
            err_msg = str(e)
            logger.error(f"Processing failed for document {doc_id}: {err_msg}", exc_info=True)
            repository.update_document_status(db, doc_id, status="failed", error_message=err_msg)

    @classmethod
    def delete_document_full(cls, db: Session, doc_id: str) -> bool:
        doc = repository.get_document(db, doc_id)
        if not doc:
            return False

        # 1. Remove from vector index
        try:
            vector_store.delete_document(doc_id)
        except Exception as e:
            logger.warning(f"Failed to remove doc {doc_id} from vector store: {e}")

        # 2. Delete file from storage
        try:
            if doc.file_path and os.path.exists(doc.file_path):
                os.remove(doc.file_path)
            for red in doc.redactions:
                if red.redacted_file_path and os.path.exists(red.redacted_file_path):
                    os.remove(red.redacted_file_path)
        except Exception as e:
            logger.warning(f"Failed to remove file {doc.file_path}: {e}")

        # 3. Delete from database
        return repository.delete_document(db, doc_id)

