from __future__ import annotations

import io
from pathlib import Path
from typing import Any


def extract_pdf_text(filepath: Path) -> tuple[str, list[dict[str, Any]]]:
    pages: list[dict[str, Any]] = []
    text_parts: list[str] = []

    try:
        import fitz  # PyMuPDF

        with fitz.open(filepath) as doc:
            for i, page in enumerate(doc, start=1):
                content = (page.get_text("text") or "").strip()
                if not content:
                    content = _ocr_page(page)
                pages.append({"page_number": i, "text": content})
                text_parts.append(content)
        text = "\n".join(text_parts).strip()
        if text:
            return text, pages
    except Exception:
        pass

    try:
        import pdfplumber

        with pdfplumber.open(filepath) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                content = (page.extract_text() or "").strip()
                pages.append({"page_number": i, "text": content})
                text_parts.append(content)
        return "\n".join(text_parts).strip(), pages
    except Exception:
        return "", []


def _ocr_page(page: Any) -> str:
    try:
        import pytesseract

        pix = page.get_pixmap(dpi=220)
        from PIL import Image

        image = Image.open(io.BytesIO(pix.tobytes("png")))
        return (pytesseract.image_to_string(image) or "").strip()
    except Exception:
        return ""


def extract_docx_text(filepath: Path) -> tuple[str, list[dict[str, Any]]]:
    try:
        from docx import Document

        doc = Document(str(filepath))
        text = "\n".join([p.text for p in doc.paragraphs if p.text]).strip()
        return text, [{"page_number": 1, "text": text}]
    except Exception:
        return "", []


def extract_txt_text(filepath: Path) -> tuple[str, list[dict[str, Any]]]:
    try:
        text = filepath.read_text(encoding="utf-8", errors="ignore")
        return text, [{"page_number": 1, "text": text}]
    except Exception:
        return "", []


def extract_document_text(filepath: Path, file_type: str) -> tuple[str, list[dict[str, Any]]]:
    if file_type == "pdf":
        return extract_pdf_text(filepath)
    if file_type == "docx":
        return extract_docx_text(filepath)
    return extract_txt_text(filepath)
