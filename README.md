# DocuIntellect – Enterprise AI Document Intelligence Platform

DocuIntellect is a local-first NLP document intelligence platform (CSE472 project by **Hariom and Ayush Singh**) built with:

- **Frontend:** React 19 + Vite
- **Backend:** FastAPI + SQLAlchemy 2.0 + SQLite
- **NLP:** spaCy, Sentence Transformers, FAISS, local NLI-compatible consistency checks
- **Document processing:** PyMuPDF, pdfplumber, python-docx, pytesseract

## Features

- Upload and manage PDF/DOCX/TXT documents
- Text extraction and OCR fallback for scanned PDFs
- Document classification and summarization
- Named entity extraction
- Hybrid semantic + lexical search
- Grounded QA over retrieved chunks with source attribution
- Privacy scanner for potential sensitive information with risk levels
- Human review workflow for findings (Confirmed Sensitive / Not Sensitive / Needs Review)
- Selective redaction and redacted export (including permanent PDF redaction + verification)
- Privacy reporting (risk and type distributions)
- Cross-document contradiction and consistency detection

> Important: Pattern detections identify **potential** sensitive information and do not prove an identifier is genuine.

## Local Setup

### Backend

```bash
cd /home/runner/work/AI-Document-Intelligence-System/AI-Document-Intelligence-System/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python run.py
```

API runs at `http://localhost:8000`.

### Frontend

```bash
cd /home/runner/work/AI-Document-Intelligence-System/AI-Document-Intelligence-System/frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173` and calls backend at `http://localhost:8000` by default.

Optional override:

```bash
VITE_API_BASE=http://localhost:8000 npm run dev
```

## Tests

```bash
cd /home/runner/work/AI-Document-Intelligence-System/AI-Document-Intelligence-System/backend
pytest -q
```
