from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PATTERNS: dict[str, re.Pattern[str]] = {
    "Email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "Phone": re.compile(r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b"),
    "PAN-like": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),
    "Aadhaar-like": re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
    "Bank Account-like": re.compile(r"\b\d{9,18}\b"),
    "IFSC": re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),
    "Passport-like": re.compile(r"\b[A-PR-WY][1-9]\d{6}\b"),
    "Address": re.compile(r"\b\d{1,4}\s+[^\n,]{3,40}(?:Road|Rd|Street|St|Lane|Ln|Avenue|Ave)\b", re.I),
}

RISK_MAP = {
    "PAN-like": "High",
    "Aadhaar-like": "High",
    "Bank Account-like": "High",
    "IFSC": "High",
    "Passport-like": "High",
    "Email": "Medium",
    "Phone": "Medium",
    "Address": "Medium",
    "Person": "Low",
}


@dataclass
class Finding:
    value: str
    masked_value: str
    info_type: str
    page_number: int
    detection_method: str
    risk_level: str
    explanation: str
    score: float


def mask_value(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def _contextual_ok(info_type: str, value: str) -> bool:
    if info_type == "Bank Account-like":
        return not (len(value) == 10 and value.startswith(("6", "7", "8", "9")))
    if info_type == "Aadhaar-like":
        digits = re.sub(r"\D", "", value)
        return len(set(digits)) > 1
    return True


def scan_sensitive_info(text: str, pages: list[dict[str, Any]], entities: list[dict[str, Any]]) -> list[Finding]:
    findings: list[Finding] = []
    page_lookup: list[tuple[int, str]] = [(p["page_number"], p.get("text", "")) for p in pages] or [(1, text)]

    for info_type, regex in PATTERNS.items():
        for m in regex.finditer(text):
            value = m.group(0)
            if not _contextual_ok(info_type, value):
                continue
            page_number = 1
            for pno, ptxt in page_lookup:
                if value in ptxt:
                    page_number = pno
                    break
            findings.append(
                Finding(
                    value=value,
                    masked_value=mask_value(value),
                    info_type=info_type,
                    page_number=page_number,
                    detection_method="Regex + contextual validation",
                    risk_level=RISK_MAP.get(info_type, "Low"),
                    explanation=(
                        f"Pattern-based match indicates potential {info_type}. "
                        "This does not prove the identifier is genuine and requires human review."
                    ),
                    score=0.84 if RISK_MAP.get(info_type) == "High" else 0.64,
                )
            )

    for ent in entities:
        if ent.get("label") in {"PERSON"}:
            value = ent["text"]
            if len(value.split()) > 4:
                continue
            findings.append(
                Finding(
                    value=value,
                    masked_value=mask_value(value),
                    info_type="Person",
                    page_number=_page_for_value(value, page_lookup),
                    detection_method="spaCy NER",
                    risk_level=RISK_MAP["Person"],
                    explanation="Named entity recognized as a person name. Requires human confirmation.",
                    score=0.58,
                )
            )

    deduped: dict[tuple[str, str, int], Finding] = {}
    for f in findings:
        deduped[(f.value, f.info_type, f.page_number)] = f
    return list(deduped.values())


def _page_for_value(value: str, page_lookup: list[tuple[int, str]]) -> int:
    for pno, ptxt in page_lookup:
        if value in ptxt:
            return pno
    return 1


def privacy_report(findings: list[dict[str, Any]]) -> dict[str, Any]:
    risk_counter = Counter(f["risk_level"] for f in findings)
    type_counter = Counter(f["info_type"] for f in findings)
    return {
        "total_findings": len(findings),
        "risk_distribution": dict(risk_counter),
        "type_distribution": dict(type_counter),
        "needs_review": sum(1 for f in findings if f.get("review_status") == "Needs Review"),
    }


def redact_pdf(
    source_path: Path,
    target_path: Path,
    values_to_redact: list[str],
) -> tuple[bool, str]:
    try:
        import fitz

        with fitz.open(source_path) as doc:
            for page in doc:
                for value in values_to_redact:
                    for rect in page.search_for(value):
                        page.add_redact_annot(rect, fill=(0, 0, 0))
                page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
            doc.save(target_path)

        extracted = _extract_pdf_text_simple(target_path)
        for value in values_to_redact:
            if value and value in extracted:
                return False, "Redaction verification failed: original text remains extractable."
        return True, "Redaction complete and verified via text extraction."
    except Exception as exc:
        return False, f"Redaction failed: {exc}"


def _extract_pdf_text_simple(path: Path) -> str:
    try:
        import fitz

        with fitz.open(path) as doc:
            return "\n".join(page.get_text("text") for page in doc)
    except Exception:
        return ""


def redact_txt_or_docx(source_path: Path, target_path: Path, values_to_redact: list[str]) -> tuple[bool, str]:
    suffix = source_path.suffix.lower()
    if suffix == ".txt":
        data = source_path.read_text(encoding="utf-8", errors="ignore")
        for value in values_to_redact:
            data = data.replace(value, "[REDACTED]")
        target_path.write_text(data, encoding="utf-8")
        return True, "TXT redaction complete."

    if suffix == ".docx":
        from docx import Document

        doc = Document(str(source_path))
        for p in doc.paragraphs:
            text = p.text
            for value in values_to_redact:
                text = text.replace(value, "[REDACTED]")
            p.text = text
        doc.save(str(target_path))
        return True, "DOCX redaction complete."

    return False, "Unsupported file type for this redaction path."
