import os
import io
import re
import shutil
import zipfile
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional

import pymupdf as fitz  # PyMuPDF
import docx  # python-docx

logger = logging.getLogger(__name__)

# Safely check if tesseract binary and pytesseract are available without blocking
HAS_PYTESSERACT = False
try:
    import pytesseract
    from PIL import Image
    # Check if tesseract binary exists on PATH or standard Windows location
    tesseract_path = shutil.which("tesseract") or shutil.which(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        HAS_PYTESSERACT = True
        logger.info(f"Tesseract OCR enabled: {tesseract_path}")
    else:
        logger.info("Tesseract binary not found on PATH. OCR fallback disabled; direct text extraction active.")
except ImportError:
    logger.info("pytesseract or PIL not installed.")

class DocumentExtractor:
    """
    Page-aware text extraction for PDF, DOCX, and TXT files.
    Includes OCR fallback for scanned PDFs when Tesseract is available.
    """

    @staticmethod
    def extract(file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        if ext == ".pdf":
            return DocumentExtractor._extract_pdf(path)
        elif ext in [".docx", ".doc"]:
            return DocumentExtractor._extract_docx(path)
        elif ext == ".txt":
            return DocumentExtractor._extract_txt(path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @staticmethod
    def _extract_pdf(path: Path) -> Dict[str, Any]:
        pages_data: List[Dict[str, Any]] = []
        doc = fitz.open(str(path))
        page_count = len(doc)
        full_text_list = []
        needs_ocr = False

        for page_idx in range(page_count):
            page = doc[page_idx]
            page_text = page.get_text("text").strip()

            # If page text is very sparse, it might be a scanned image
            if len(page_text) < 30 and HAS_PYTESSERACT:
                logger.info(f"Page {page_idx + 1} has minimal text ({len(page_text)} chars); attempting OCR...")
                ocr_text = DocumentExtractor._ocr_pdf_page(page)
                if ocr_text and len(ocr_text) > len(page_text):
                    page_text = ocr_text
                    needs_ocr = True

            pages_data.append({
                "page_number": page_idx + 1,
                "text": page_text
            })
            if page_text:
                full_text_list.append(page_text)

        doc.close()
        full_text = "\n\n".join(full_text_list).strip()

        if not full_text:
            if not HAS_PYTESSERACT:
                raise ValueError("PDF contains no selectable text (scanned document) and OCR engine is unavailable.")
            else:
                raise ValueError("No usable text could be extracted from PDF even after OCR analysis.")

        return {
            "page_count": max(page_count, 1),
            "pages": pages_data,
            "full_text": full_text,
            "used_ocr": needs_ocr
        }

    @staticmethod
    def _ocr_pdf_page(page: fitz.Page) -> str:
        try:
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception as e:
            logger.warning(f"OCR failed for page: {e}")
            return ""

    @staticmethod
    def _extract_docx(path: Path) -> Dict[str, Any]:
        paragraphs: List[str] = []
        extraction_method = "python-docx"

        # 1. Primary Attempt: Standard python-docx library
        try:
            doc = docx.Document(str(path))
            for p in doc.paragraphs:
                if p.text and p.text.strip():
                    paragraphs.append(p.text.strip())
            # Also extract tables (resumes, templates, IEEE papers)
            for table in doc.tables:
                for row in table.rows:
                    row_cells = [c.text.strip() for c in row.cells if c.text.strip()]
                    if row_cells:
                        paragraphs.append(" | ".join(row_cells))
        except Exception as docx_err:
            logger.warning(
                f"Standard python-docx parser failed for '{path.name}' ({docx_err}); "
                "attempting robust direct XML OpenXML fallback..."
            )
            paragraphs = []

        # 2. Fallback: Direct XML extraction from ZIP (handles ISO/IEC 29500 Strict OOXML, IEEE templates, etc.)
        if not paragraphs and zipfile.is_zipfile(str(path)):
            try:
                with zipfile.ZipFile(str(path)) as z:
                    doc_xml_name = None
                    for candidate in ["word/document.xml", "document.xml"]:
                        if candidate in z.namelist():
                            doc_xml_name = candidate
                            break
                    if not doc_xml_name:
                        for name in z.namelist():
                            if name.endswith("document.xml"):
                                doc_xml_name = name
                                break

                    if doc_xml_name:
                        xml_bytes = z.read(doc_xml_name)
                        root = ET.fromstring(xml_bytes)
                        for elem in root.iter():
                            if elem.tag.endswith("}p"):
                                parts = []
                                for child in elem.iter():
                                    if child.tag.endswith("}t") and child.text:
                                        parts.append(child.text)
                                    elif child.tag.endswith("}tab"):
                                        parts.append(" ")
                                    elif child.tag.endswith("}br"):
                                        parts.append("\n")
                                p_text = "".join(parts).strip()
                                if p_text:
                                    paragraphs.append(p_text)
                        if paragraphs:
                            extraction_method = "openxml-direct-fallback"
                            logger.info(f"Direct OpenXML fallback successfully extracted {len(paragraphs)} paragraphs from {path.name}.")
            except Exception as xml_err:
                logger.warning(f"Direct XML extraction failed: {xml_err}")

        # 3. Fallback for legacy binary .doc or RTF documents
        if not paragraphs:
            try:
                with open(path, "rb") as f:
                    header = f.read(16)
                    # RTF check
                    if header.startswith(b"{\\rtf"):
                        f.seek(0)
                        raw_rtf = f.read().decode("latin-1", errors="ignore")
                        clean_rtf = re.sub(r"\\[a-z]+(-?\d+)? ?", " ", raw_rtf)
                        clean_rtf = re.sub(r"[{}]", "", clean_rtf)
                        lines = [line.strip() for line in clean_rtf.splitlines() if len(line.strip()) > 3]
                        if lines:
                            paragraphs = lines
                            extraction_method = "rtf-fallback"
                    # Binary strings extraction for older OLE .doc files
                    else:
                        f.seek(0)
                        raw_bytes = f.read()
                        ascii_strings = re.findall(rb"[\x20-\x7E\s]{6,}", raw_bytes)
                        valid_lines = [
                            s.decode("latin-1", errors="ignore").strip()
                            for s in ascii_strings
                            if len(s.decode("latin-1", errors="ignore").strip()) > 15
                        ]
                        if valid_lines:
                            paragraphs = valid_lines
                            extraction_method = "binary-strings-fallback"
            except Exception as legacy_err:
                logger.warning(f"Legacy file inspection failed: {legacy_err}")

        full_text = "\n\n".join(paragraphs).strip()
        if not full_text:
            raise ValueError("DOCX document appears to be empty or contains no readable text.")

        chars_per_page = 2500
        pages_data = []
        current_page_text = []
        current_len = 0
        current_page_num = 1

        for p in paragraphs:
            current_page_text.append(p)
            current_len += len(p)
            if current_len >= chars_per_page:
                pages_data.append({
                    "page_number": current_page_num,
                    "text": "\n\n".join(current_page_text).strip()
                })
                current_page_num += 1
                current_page_text = []
                current_len = 0

        if current_page_text or not pages_data:
            pages_data.append({
                "page_number": current_page_num,
                "text": "\n\n".join(current_page_text).strip()
            })

        logger.info(f"DOCX extraction completed using '{extraction_method}' ({len(pages_data)} pages, {len(full_text)} chars).")

        return {
            "page_count": len(pages_data),
            "pages": pages_data,
            "full_text": full_text,
            "used_ocr": False
        }

    @staticmethod
    def _extract_txt(path: Path) -> Dict[str, Any]:
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        content = None
        for enc in encodings:
            try:
                with open(str(path), "r", encoding=enc) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if content is None:
            raise ValueError("Unable to decode text file with standard encodings.")

        content = content.strip()
        if not content:
            raise ValueError("TXT document is empty.")

        chars_per_page = 2500
        pages_data = []
        lines = content.splitlines()
        current_lines = []
        current_len = 0
        current_page_num = 1

        for line in lines:
            current_lines.append(line)
            current_len += len(line)
            if current_len >= chars_per_page:
                pages_data.append({
                    "page_number": current_page_num,
                    "text": "\n".join(current_lines).strip()
                })
                current_page_num += 1
                current_lines = []
                current_len = 0

        if current_lines or not pages_data:
            pages_data.append({
                "page_number": current_page_num,
                "text": "\n".join(current_lines).strip()
            })

        return {
            "page_count": len(pages_data),
            "pages": pages_data,
            "full_text": content,
            "used_ocr": False
        }
