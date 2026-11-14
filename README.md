# AI Document Intelligence System (DocuIntellect)

A modular, enterprise-grade AI-powered document analysis system and Retrieval-Augmented Generation (RAG) web application.

> **Technical Architecture & Module Guide**: See [ARCHITECTURE_AND_FEATURES.md](file:///D:/AI%20Document%20Intelligence%20System/ARCHITECTURE_AND_FEATURES.md) for full module connectivity graphs, Mermaid pipeline diagrams, database schemas, and API contracts.

---

### Quick Start (All-in-One Command)

```bash
npm run dev
```
- **Frontend**: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- **Backend API & Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 1. Technology Stack

| Layer | Technology | Responsibility |
|---|---|---|
| **Frontend** | React.js (Vite) + Lucide Icons | Responsive dashboard, document viewer, upload, RAG chat, and semantic search |
| **UI Styling** | Modern CSS | Clean responsive layout with status badges, tabs, and citation cards |
| **Backend** | Python + FastAPI | High-performance asynchronous REST API, validation, and pipeline coordination |
| **PDF Processing** | PyMuPDF (`pymupdf`) | Page-aware text extraction and metadata parsing |
| **DOCX/TXT Processing** | `python-docx`, native Python | Text extraction with pagination approximations |
| **OCR Fallback** | Tesseract + `pytesseract` | OCR processing for scanned documents |
| **Summarization** | Hugging Face Transformers / Extractive Ranker | Generation of short summaries, detailed overviews, and key takeaways |
| **Entity Extraction** | spaCy (`en_core_web_sm`) | Named entity recognition (PERSON, ORG, GPE, DATE, MONEY, etc.) |
| **Classification** | scikit-learn | TF-IDF + Naive Bayes probabilistic document categorization |
| **Semantic Search & RAG** | Sentence Transformers + FAISS | Dense vector representations (`all-MiniLM-L6-v2`) and cosine similarity index |
| **Privacy & Security** | Hybrid Regex + spaCy + PyMuPDF | Sensitive data detection (PAN, Aadhaar, Bank, IFSC, Passport, Phone, Email), risk classification & permanent redaction |
| **Contradiction Detection** | Cross-Encoder (`nli-deberta-v3-base`) + MiniLM | Cross-document NLI classification, candidate pair matching & neuro-symbolic polarity guardrails |
| **Numerical Consistency** | Regex Normalizer + Contextual Parser | Multi-currency (INR/USD/EUR/GBP), date, percentage & duration reconciliation |
| **Database** | SQLite + SQLAlchemy 2.0 | Persistent storage for document metadata, analysis results, privacy findings, consistency jobs, conflicts, and chat history |
| **Testing** | `pytest` | Unit, integration, benchmark (precision/recall/F1), and end-to-end pipeline verification |

---

## 2. Architecture & Pipeline

```
[User / Browser]
       │
       ▼
[React + Vite Frontend]
       │
       ▼ (REST API)
[FastAPI Backend Application]
       │
       ├─► 1. Document Storage (`data/uploads/`)
       ├─► 2. Page-Aware Text Extraction (`PyMuPDF` / `python-docx` / OCR)
       ├─► 3. Cleaning & Sentence Boundary Chunking (`preprocessor.py`)
       ├─► 4. AI NLP Processing:
       │      ├─ Summarizer (Short, Detailed, Key Points)
       │      ├─ spaCy NER (Entities + Page numbers)
       │      └─ scikit-learn Document Classifier
       ├─► 5. Dense Embeddings (`sentence-transformers/all-MiniLM-L6-v2`)
       ├─► 6. FAISS Vector Store (`data/indexes/faiss.index`)
       ├─► 7. AI Privacy & Sensitive Info Scanner (`privacy_scanner.py`, `risk_classifier.py`)
       │      └─ Permanent Redaction & Verification Engine (`document_redactor.py`)
       ├─► 8. RAG Question Answering with Citations (`qa_service.py`)
       ├─► 9. AI Cross-Document Contradiction & Consistency Detector:
       │      ├─ Semantic Candidate Pair Retrieval (`statement_matcher.py`)
       │      ├─ Local Cross-Encoder NLI Engine (`contradiction_detector.py`)
       │      ├─ Numerical, Date & Currency Normalizer (`numerical_consistency.py`)
       │      └─ Multi-Document Audit & Review Workflow (`conflict_reporter.py`)
       └─► 10. SQLite Relational Persistence (`data/app.db`)
```

---

## 3. Repository Structure

```
ai-document-intelligence/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUploader.jsx       # Drag & drop upload with validation
│   │   │   ├── SummaryPanel.jsx       # AI summary & bullet points
│   │   │   ├── EntityPanel.jsx        # spaCy entity filter & display
│   │   │   ├── ChatPanel.jsx          # Interactive RAG chat
│   │   │   ├── SourceCitation.jsx     # Grounded evidence cards with page refs
│   │   │   ├── PrivacyScanner.jsx     # AI privacy & sensitive info scanner workspace
│   │   │   ├── PrivacyReport.jsx      # Privacy executive summary & risk metrics
│   │   │   ├── PrivacyFindingCard.jsx # Masked sensitive finding card & actions
│   │   │   ├── RedactionPreview.jsx   # Permanent redaction modal & download
│   │   │   ├── RiskDistribution.jsx   # Risk levels & category filter chips
│   │   │   ├── ConsistencyDashboard.jsx # Cross-doc contradiction KPI metrics & breakdown
│   │   │   ├── DocumentComparisonSelector.jsx # Multi-document selection & compare triggers
│   │   │   ├── ConflictCard.jsx       # Side-by-side contradiction evidence cards
│   │   │   ├── StatementComparison.jsx # Statement A vs Statement B diff view
│   │   │   ├── ConflictEvidence.jsx   # Numerical difference & explanation context
│   │   │   ├── ConsistencyFilters.jsx # Conflict category, status & search filters
│   │   │   ├── ReviewStatus.jsx       # Human decision status updater dropdown
│   │   │   └── Navbar.jsx             # Navigation header & live health status
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx          # Metric cards, categories, quick upload
│   │   │   ├── DocumentLibrary.jsx    # Table, status filter, retry & delete
│   │   │   ├── DocumentDetail.jsx     # Tabbed intelligence & privacy view
│   │   │   ├── DocumentChat.jsx       # Dedicated document chat interface
│   │   │   ├── SearchPage.jsx         # Semantic natural language search
│   │   │   └── ConsistencyAnalyzer.jsx # Cross-document contradiction audit page
│   │   ├── services/
│   │   │   └── api.js                 # Frontend API client
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   │   ├── documents.py           # Upload, list, detail, results, delete
│   │   │   ├── summary.py             # Re-summarization endpoint
│   │   │   ├── chat.py                # Document Q&A and chat history
│   │   │   ├── search.py              # Semantic vector search endpoint
│   │   │   ├── privacy.py             # Privacy scan, review, redact & download
│   │   │   └── consistency.py         # Cross-document contradiction & consistency
│   │   ├── services/
│   │   │   ├── document_service.py    # Lifecycle & pipeline orchestrator
│   │   │   ├── extractor.py           # PDF/DOCX/TXT/OCR extraction
│   │   │   ├── preprocessor.py        # Text normalization & chunking
│   │   │   ├── summarizer.py          # Summary & key points generator
│   │   │   ├── ner.py                 # spaCy entity extraction
│   │   │   ├── classifier.py          # scikit-learn classifier
│   │   │   ├── embeddings.py          # Dense vector representations
│   │   │   ├── vector_store.py        # FAISS / NumPy index persistence & search
│   │   │   ├── retriever.py           # Ranked passage retrieval
│   │   │   ├── qa_service.py          # Grounded RAG answering
│   │   │   ├── privacy_scanner.py     # Hybrid sensitive information detector
│   │   │   ├── risk_classifier.py     # Risk classification & non-revealing masking
│   │   │   ├── document_redactor.py   # Byte-level permanent PDF/DOCX/TXT redaction
│   │   │   ├── statement_matcher.py   # Page-associated statement candidate matcher
│   │   │   ├── contradiction_detector.py # Local DeBERTa-v3 Cross-Encoder NLI
│   │   │   ├── numerical_consistency.py # Monetary, calendar date & duration analyzer
│   │   │   └── conflict_reporter.py   # Multi-document consistency auditor & reporting
│   │   ├── db/
│   │   │   ├── database.py            # SQLAlchemy engine & session
│   │   │   ├── models.py              # ORM models (Document, PrivacyFinding, Conflicts, Jobs)
│   │   │   └── repository.py          # CRUD database access
│   │   ├── core/
│   │   │   └── config.py              # Pydantic settings & directories
│   │   └── main.py                    # FastAPI application entrypoint
│   ├── tests/
│   │   ├── test_services.py           # NLP components unit tests
│   │   ├── test_privacy.py            # Privacy detection & redaction tests (13 tests)
│   │   ├── test_consistency.py        # Cross-document consistency & NLI benchmark (13 tests)
│   │   ├── test_consistency_api.py    # Consistency REST API full lifecycle tests
│   │   ├── test_api.py                # REST API endpoints test
│   │   └── test_end_to_end.py         # Full pipeline integration test
│   └── requirements.txt
│
├── data/                              # Local runtime data
│   ├── uploads/                       # Private document files
│   ├── redacted/                      # Verified sanitized redacted documents
│   ├── indexes/                       # FAISS index & metadata
│   └── app.db                         # SQLite database
├── .gitignore
├── .env.example
└── README.md
```

---

## 4. Getting Started

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Node.js 18+ and npm
- (Optional) Tesseract OCR installed on PATH for scanned PDF optical character recognition

### Backend Setup
1. Open a terminal and navigate to the project root:
   ```bash
   cd "D:\AI Document Intelligence System"
   ```

2. Activate the Python virtual environment:
   ```powershell
   # Windows PowerShell
   .\backend\venv\Scripts\Activate.ps1
   ```

3. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   python -m spacy download en_core_web_sm
   ```

4. Start the FastAPI backend server:
   ```powershell
   $env:PYTHONPATH="backend"
   .\backend\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   The API will be available at: `http://127.0.0.1:8000`
   Interactive OpenAPI documentation: `http://127.0.0.1:8000/docs`

---

### Frontend Setup
1. In a new terminal, navigate to the `frontend` folder:
   ```bash
   cd "D:\AI Document Intelligence System\frontend"
   ```

2. Install npm dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

## 5. API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/documents/upload` | Upload PDF/DOCX/TXT and initiate background processing |
| `GET` | `/api/documents` | List all documents with status and categories |
| `GET` | `/api/documents/{id}` | Get status and metadata for a specific document |
| `GET` | `/api/documents/{id}/results` | Get all extracted intelligence (summaries, entities, classification) |
| `POST` | `/api/documents/{id}/summarize` | Regenerate summary and key bullet points |
| `POST` | `/api/documents/{id}/ask` | Ask questions with grounded source citations and page numbers |
| `GET` | `/api/documents/{id}/history` | Get previous question and answer history |
| `POST` | `/api/search` | Semantic natural language search across document chunks |
| `DELETE` | `/api/documents/{id}` | Delete document, physical file, FAISS index, and redacted copies |
| `GET` | `/api/health` | Service health status |
| `GET` | `/api/documents/{id}/privacy` | Get structured privacy risk report and sensitive findings |
| `POST` | `/api/documents/{id}/privacy/scan` | Trigger or re-run on-demand privacy and PII scan |
| `PATCH` | `/api/privacy/findings/{finding_id}` | Update human review status (`confirmed_sensitive`, `not_sensitive`, etc.) |
| `POST` | `/api/documents/{id}/privacy/redact` | Execute byte-level permanent redaction with verification |
| `GET` | `/api/documents/{id}/privacy/redacted` | Retrieve history of redacted documents |
| `GET` | `/api/privacy/download/{redaction_id}` | Securely stream and download verified redacted PDF/DOCX/TXT |
| `POST` | `/api/intelligence/consistency/analyze` | Start cross-document consistency & contradiction analysis |
| `GET` | `/api/intelligence/consistency/{analysis_id}` | Poll progress, metrics, and findings of analysis job |
| `GET` | `/api/intelligence/conflicts` | List, search, and filter identified contradictions |
| `GET` | `/api/intelligence/conflicts/{conflict_id}` | Get complete side-by-side evidence context for conflict |
| `PATCH` | `/api/intelligence/conflicts/{conflict_id}` | Update human review status (`confirmed_conflict`, `valid_revision`, etc.) |
| `POST` | `/api/intelligence/consistency/compare` | Direct pairwise document contradiction comparison |

---

## 6. Running Tests

Run backend unit tests, privacy tests, and end-to-end integration tests:
```powershell
$env:PYTHONPATH="backend"
# Run NLP unit tests
.\backend\venv\Scripts\python.exe -m pytest backend/tests/test_services.py -v

# Run Privacy Scanner & Redaction test suite (13 tests including precision/recall benchmark)
.\backend\venv\Scripts\python.exe -m pytest backend/tests/test_privacy.py -v

# Run Cross-Document Consistency & Contradiction test suite (13 unit tests + precision/recall/F1 benchmark)
.\backend\venv\Scripts\python.exe -m pytest backend/tests/test_consistency.py -v

# Run Consistency REST API Lifecycle integration test
.\backend\venv\Scripts\python.exe -m pytest backend/tests/test_consistency_api.py -v

# Run API endpoint tests
.\backend\venv\Scripts\python.exe backend/tests/test_api.py

# Run Full End-to-End Pipeline test
.\backend\venv\Scripts\python.exe backend/tests/test_end_to_end.py
```

