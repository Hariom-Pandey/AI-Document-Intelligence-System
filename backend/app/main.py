from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Document, DocumentChunk, SensitiveFinding
from .schemas import ComparisonRequest, FindingStatusUpdate, QuestionRequest, SearchRequest, SummaryResponse
from .services.document_processing import extract_document_text
from .services.nlp import (
    answer_question,
    chunk_text,
    classify_document,
    extract_entities,
    hybrid_search,
    local_nli_relation,
    summarize_text,
    vector_from_json,
    vector_to_json,
    embed_texts,
)
from .services.privacy import privacy_report, redact_pdf, redact_txt_or_docx, scan_sensitive_info

app = FastAPI(title="DocuIntellect API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / "storage" / "uploads"
EXPORT_DIR = BASE_DIR / "storage" / "exports"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health():
    return {"status": "ok", "service": "DocuIntellect"}


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    ext = Path(file.filename or "").suffix.lower().lstrip(".")
    if ext not in {"pdf", "docx", "txt"}:
        raise HTTPException(status_code=400, detail="Only PDF, DOCX and TXT are supported.")

    safe_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{Path(file.filename).name}"
    target = UPLOAD_DIR / safe_name
    target.write_bytes(await file.read())

    text, pages = extract_document_text(target, ext)
    category = classify_document(text)
    summary = summarize_text(text, category)

    doc = Document(
        filename=file.filename or safe_name,
        filepath=str(target),
        file_type=ext,
        category=category,
        summary=summary,
        text_content=text,
        processing_status="processed" if text else "empty",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    chunks = chunk_text(text)
    vectors = embed_texts(chunks)
    for idx, chunk in enumerate(chunks):
        page_no = 1
        for p in pages:
            if chunk[:40] and chunk[:40] in p.get("text", ""):
                page_no = p["page_number"]
                break
        db.add(
            DocumentChunk(
                document_id=doc.id,
                page_number=page_no,
                chunk_index=idx,
                content=chunk,
                vector_json=vector_to_json(vectors[idx]),
            )
        )
    db.commit()

    return {"document_id": doc.id, "filename": doc.filename, "category": doc.category, "summary": doc.summary}


@app.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "file_type": d.file_type,
            "category": d.category,
            "processing_status": d.processing_status,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


@app.get("/documents/{document_id}")
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    entities = extract_entities(doc.text_content)
    return {
        "id": doc.id,
        "filename": doc.filename,
        "category": doc.category,
        "summary": doc.summary,
        "text_content": doc.text_content,
        "entities": entities,
    }


@app.delete("/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    path = Path(doc.filepath)
    if path.exists():
        path.unlink()
    db.delete(doc)
    db.commit()
    return {"deleted": True}


@app.post("/documents/{document_id}/summary", response_model=SummaryResponse)
def regenerate_summary(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    doc.summary = summarize_text(doc.text_content, doc.category)
    db.commit()
    return SummaryResponse(document_id=doc.id, category=doc.category, summary=doc.summary)


@app.get("/documents/{document_id}/entities")
def document_entities(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"document_id": doc.id, "entities": extract_entities(doc.text_content)}


@app.post("/search")
def semantic_search(payload: SearchRequest, db: Session = Depends(get_db)):
    chunks = db.query(DocumentChunk).all()
    chunk_rows = []
    for c in chunks:
        d = db.query(Document).filter(Document.id == c.document_id).first()
        chunk_rows.append(
            {
                "chunk_id": c.id,
                "document_id": c.document_id,
                "document_name": d.filename if d else "Unknown",
                "page_number": c.page_number,
                "content": c.content,
                "vector": vector_from_json(c.vector_json),
            }
        )
    results = hybrid_search(payload.query, chunk_rows, payload.top_k)
    return {"query": payload.query, "results": results}


@app.post("/qa")
def grounded_qa(payload: QuestionRequest, db: Session = Depends(get_db)):
    search = semantic_search(SearchRequest(query=payload.question, top_k=payload.top_k), db)
    answer = answer_question(payload.question, search["results"])
    return {"question": payload.question, **answer}


@app.post("/privacy/scan/{document_id}")
def run_privacy_scan(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    db.query(SensitiveFinding).filter(SensitiveFinding.document_id == document_id).delete()
    entities = extract_entities(doc.text_content)
    findings = scan_sensitive_info(doc.text_content, [{"page_number": 1, "text": doc.text_content}], entities)

    for f in findings:
        db.add(
            SensitiveFinding(
                document_id=document_id,
                value=f.value,
                masked_value=f.masked_value,
                info_type=f.info_type,
                page_number=f.page_number,
                detection_method=f.detection_method,
                risk_level=f.risk_level,
                explanation=f.explanation,
                score=f.score,
            )
        )
    db.commit()
    return {"document_id": document_id, "count": len(findings)}


@app.get("/privacy/findings/{document_id}")
def get_findings(document_id: int, db: Session = Depends(get_db)):
    rows = db.query(SensitiveFinding).filter(SensitiveFinding.document_id == document_id).all()
    return {
        "document_id": document_id,
        "findings": [
            {
                "id": r.id,
                "masked_value": r.masked_value,
                "value": r.value,
                "info_type": r.info_type,
                "page_number": r.page_number,
                "detection_method": r.detection_method,
                "risk_level": r.risk_level,
                "explanation": r.explanation,
                "review_status": r.review_status,
                "selected_for_redaction": r.selected_for_redaction,
                "score": r.score,
            }
            for r in rows
        ],
    }


@app.patch("/privacy/findings/{finding_id}")
def update_finding(finding_id: int, payload: FindingStatusUpdate, db: Session = Depends(get_db)):
    row = db.query(SensitiveFinding).filter(SensitiveFinding.id == finding_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Finding not found.")
    row.review_status = payload.review_status
    if payload.selected_for_redaction is not None:
        row.selected_for_redaction = payload.selected_for_redaction
    db.commit()
    return {"updated": True}


@app.post("/privacy/redact/{document_id}")
def redact_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    findings = (
        db.query(SensitiveFinding)
        .filter(SensitiveFinding.document_id == document_id, SensitiveFinding.selected_for_redaction.is_(True))
        .all()
    )
    if not findings:
        raise HTTPException(status_code=400, detail="No selected findings for redaction.")

    source = Path(doc.filepath)
    target = EXPORT_DIR / f"redacted_{source.name}"
    values = [f.value for f in findings if f.review_status != "Not Sensitive"]

    if doc.file_type == "pdf":
        ok, message = redact_pdf(source, target, values)
    else:
        ok, message = redact_txt_or_docx(source, target, values)

    if not ok:
        raise HTTPException(status_code=500, detail=message)

    return {"message": message, "export_path": str(target), "download_url": f"/privacy/export/{target.name}"}


@app.get("/privacy/export/{filename}")
def download_export(filename: str):
    target = EXPORT_DIR / filename
    if not target.exists():
        raise HTTPException(status_code=404, detail="Export not found.")
    return FileResponse(path=target, filename=filename)


@app.get("/privacy/report/{document_id}")
def get_privacy_report(document_id: int, db: Session = Depends(get_db)):
    rows = db.query(SensitiveFinding).filter(SensitiveFinding.document_id == document_id).all()
    findings = [
        {
            "risk_level": r.risk_level,
            "info_type": r.info_type,
            "review_status": r.review_status,
        }
        for r in rows
    ]
    return {"document_id": document_id, **privacy_report(findings)}


@app.post("/consistency/compare")
def compare_documents(payload: ComparisonRequest, db: Session = Depends(get_db)):
    if len(payload.document_ids) < 2:
        raise HTTPException(status_code=400, detail="Select at least two documents.")

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id.in_(payload.document_ids))
        .order_by(DocumentChunk.document_id, DocumentChunk.chunk_index)
        .all()
    )
    docs = {d.id: d for d in db.query(Document).filter(Document.id.in_(payload.document_ids)).all()}

    statements = [
        {
            "document_id": c.document_id,
            "document_name": docs[c.document_id].filename if c.document_id in docs else "Unknown",
            "page_number": c.page_number,
            "text": c.content,
        }
        for c in chunks
        if len(c.content) > 25
    ]

    comparisons = []
    for i in range(len(statements)):
        for j in range(i + 1, len(statements)):
            a, b = statements[i], statements[j]
            if a["document_id"] == b["document_id"]:
                continue
            relation, score, reason = local_nli_relation(a["text"], b["text"])
            if relation == "Neutral":
                continue
            comparisons.append(
                {
                    "relation": relation,
                    "confidence": round(score, 4),
                    "reason": reason,
                    "statement_a": a,
                    "statement_b": b,
                }
            )
            if len(comparisons) >= payload.max_pairs:
                break
        if len(comparisons) >= payload.max_pairs:
            break

    return {"document_ids": payload.document_ids, "comparisons": comparisons}
