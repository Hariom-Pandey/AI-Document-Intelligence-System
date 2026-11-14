import os
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

class DocumentRedactor:
    """
    Permanent document sanitization and redaction engine.
    Supports byte-level redaction for PDF (PyMuPDF) and structure-level redaction
    for DOCX and TXT files with post-redaction verification.
    """

    @classmethod
    def redact_document(
        cls,
        original_file_path: str,
        findings_to_redact: List[Dict[str, Any]],
        file_type: str = "pdf",
        redaction_label: str = "REDACTED"
    ) -> Tuple[str, str, bool, int]:
        """
        Executes permanent redaction on the specified findings.
        Returns: (redacted_file_path, redacted_filename, verification_status, redacted_count)
        """
        orig_path = Path(original_file_path).resolve()
        if not orig_path.exists():
            raise FileNotFoundError(f"Original file not found: {original_file_path}")

        # Ensure REDACTED_DIR exists
        settings.REDACTED_DIR.mkdir(parents=True, exist_ok=True)

        redaction_uuid = str(uuid.uuid4())
        ext = orig_path.suffix.lower()
        clean_base = orig_path.stem.replace(" ", "_")
        redacted_filename = f"{clean_base}_redacted_{redaction_uuid[:8]}{ext}"
        redacted_file_path = str(settings.REDACTED_DIR / redacted_filename)

        ft = file_type.lower().replace(".", "")
        if ft == "pdf":
            redacted_count, verified = cls._redact_pdf(
                str(orig_path),
                redacted_file_path,
                findings_to_redact
            )
        elif ft in ["docx", "doc"]:
            redacted_count, verified = cls._redact_docx(
                str(orig_path),
                redacted_file_path,
                findings_to_redact,
                redaction_label
            )
        else:
            redacted_count, verified = cls._redact_txt(
                str(orig_path),
                redacted_file_path,
                findings_to_redact,
                redaction_label
            )

        return redacted_file_path, redacted_filename, verified, redacted_count

    @classmethod
    def _redact_pdf(
        cls,
        input_path: str,
        output_path: str,
        findings: List[Dict[str, Any]]
    ) -> Tuple[int, bool]:
        """
        Applies permanent byte-level redactions to PDF files using PyMuPDF (fitz).
        Permanently removes underlying text glyphs, vector art, and raster pixels.
        """
        try:
            import fitz
        except ImportError:
            import pymupdf as fitz

        doc = fitz.open(input_path)
        applied_count = 0
        target_texts_by_page: Dict[int, List[str]] = {}

        for f in findings:
            raw = f.get("raw_value", "").strip()
            if not raw:
                continue
            pg = int(f.get("page_number", 1))
            if pg not in target_texts_by_page:
                target_texts_by_page[pg] = []
            target_texts_by_page[pg].append(raw)

        # Apply redactions per page
        for pg_num in range(len(doc)):
            page_index = pg_num + 1
            page = doc[pg_num]
            targets = target_texts_by_page.get(page_index, [])
            
            # Also check if any target exists across all pages (if page numbering differed)
            all_targets = [f.get("raw_value", "").strip() for f in findings if f.get("raw_value", "").strip()]
            search_targets = list(set(targets + all_targets))

            for target in search_targets:
                if len(target) < 2:
                    continue
                # Search for target text rects on page
                rects = page.search_for(target)
                if not rects and " " in target:
                    # Try partial sub-word matching for hyphenated / wrapped text
                    parts = target.split()
                    for p in parts:
                        if len(p) >= 4:
                            rects.extend(page.search_for(p))

                for rect in rects:
                    # Solid black redaction box
                    page.add_redact_annot(rect, fill=(0, 0, 0))
                    applied_count += 1

            # Irreversibly wipe underlying characters & pixels
            page.apply_redactions()

        # Save with garbage collection to purge unreferenced objects
        doc.save(output_path, garbage=4, deflate=True)
        doc.close()

        # Step 2: Verification Check through Text Extraction
        verified = cls._verify_pdf_redaction(output_path, findings)
        return applied_count, verified

    @classmethod
    def _verify_pdf_redaction(cls, redacted_pdf_path: str, findings: List[Dict[str, Any]]) -> bool:
        """
        Extracts all text from the redacted PDF to verify that none of the target
        raw sensitive values are readable or extractable.
        """
        try:
            try:
                import fitz
            except ImportError:
                import pymupdf as fitz

            verify_doc = fitz.open(redacted_pdf_path)
            extracted_text = ""
            for page in verify_doc:
                extracted_text += page.get_text() + "\n"
            verify_doc.close()

            extracted_lower = extracted_text.lower()
            for f in findings:
                raw = f.get("raw_value", "").strip().lower()
                # Check for significant tokens (length >= 5) to verify absence
                if len(raw) >= 5 and raw in extracted_lower:
                    logger.warning(f"Redaction verification failed! Raw token '{raw}' still detected in extracted text.")
                    return False

            return True
        except Exception as e:
            logger.error(f"Error during redaction verification: {e}")
            return False

    @classmethod
    def _redact_docx(
        cls,
        input_path: str,
        output_path: str,
        findings: List[Dict[str, Any]],
        redaction_label: str
    ) -> Tuple[int, bool]:
        """
        Redacts sensitive text from DOCX documents while preserving formatting.
        """
        import docx

        doc = docx.Document(input_path)
        applied_count = 0
        raw_targets = [f.get("raw_value", "").strip() for f in findings if f.get("raw_value", "").strip()]

        # Helper to redact in paragraph
        def redact_in_paragraph(p):
            nonlocal applied_count
            for target in raw_targets:
                if target in p.text:
                    p.text = p.text.replace(target, f"[████ {redaction_label} ████]")
                    applied_count += 1

        for p in doc.paragraphs:
            redact_in_paragraph(p)

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        redact_in_paragraph(p)

        doc.save(output_path)

        # Verification check
        verify_doc = docx.Document(output_path)
        verify_text = "\n".join([p.text for p in verify_doc.paragraphs]).lower()
        verified = not any(t.lower() in verify_text for t in raw_targets if len(t) >= 5)

        return applied_count, verified

    @classmethod
    def _redact_txt(
        cls,
        input_path: str,
        output_path: str,
        findings: List[Dict[str, Any]],
        redaction_label: str
    ) -> Tuple[int, bool]:
        """
        Redacts sensitive text from TXT files.
        """
        with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        applied_count = 0
        raw_targets = [f.get("raw_value", "").strip() for f in findings if f.get("raw_value", "").strip()]

        for target in raw_targets:
            if target in content:
                content = content.replace(target, f"[████ {redaction_label} ████]")
                applied_count += 1

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Verification check
        with open(output_path, "r", encoding="utf-8", errors="ignore") as f:
            verify_text = f.read().lower()

        verified = not any(t.lower() in verify_text for t in raw_targets if len(t) >= 5)
        return applied_count, verified

