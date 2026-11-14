import { useEffect, useMemo, useState } from 'react'
import './App.css'

const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, options)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || 'Request failed')
  }
  return res.json()
}

function App() {
  const [documents, setDocuments] = useState([])
  const [selectedDocId, setSelectedDocId] = useState(null)
  const [docDetails, setDocDetails] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [question, setQuestion] = useState('')
  const [qaResult, setQaResult] = useState(null)
  const [findings, setFindings] = useState([])
  const [report, setReport] = useState(null)
  const [comparisonIds, setComparisonIds] = useState([])
  const [comparisonResults, setComparisonResults] = useState([])
  const [status, setStatus] = useState('Ready')

  const selectedDoc = useMemo(
    () => documents.find((d) => d.id === selectedDocId) || null,
    [documents, selectedDocId],
  )

  const loadDocuments = async () => {
    const list = await api('/documents')
    setDocuments(list)
    if (!selectedDocId && list.length) setSelectedDocId(list[0].id)
  }

  const loadDocDetails = async (id) => {
    if (!id) return
    const details = await api(`/documents/${id}`)
    setDocDetails(details)
  }

  const loadFindings = async (id) => {
    if (!id) return
    const data = await api(`/privacy/findings/${id}`)
    setFindings(data.findings)
  }

  const loadReport = async (id) => {
    if (!id) return
    const data = await api(`/privacy/report/${id}`)
    setReport(data)
  }

  useEffect(() => {
    loadDocuments().catch((e) => setStatus(e.message))
  }, [])

  useEffect(() => {
    if (!selectedDocId) return
    Promise.all([loadDocDetails(selectedDocId), loadFindings(selectedDocId), loadReport(selectedDocId)]).catch((e) =>
      setStatus(e.message),
    )
  }, [selectedDocId])

  const onUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    const fd = new FormData()
    fd.append('file', file)
    setStatus('Uploading and processing...')
    try {
      const out = await api('/documents/upload', { method: 'POST', body: fd })
      setStatus(`Uploaded ${out.filename}`)
      await loadDocuments()
      setSelectedDocId(out.document_id)
    } catch (e) {
      setStatus(e.message)
    }
  }

  const runSearch = async () => {
    if (!searchQuery.trim()) return
    try {
      const out = await api('/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, top_k: 5 }),
      })
      setSearchResults(out.results)
    } catch (e) {
      setStatus(e.message)
    }
  }

  const runQa = async () => {
    if (!question.trim()) return
    try {
      const out = await api('/qa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, top_k: 4 }),
      })
      setQaResult(out)
    } catch (e) {
      setStatus(e.message)
    }
  }

  const runPrivacyScan = async () => {
    if (!selectedDocId) return
    try {
      setStatus('Scanning for potential sensitive information...')
      await api(`/privacy/scan/${selectedDocId}`, { method: 'POST' })
      await Promise.all([loadFindings(selectedDocId), loadReport(selectedDocId)])
      setStatus('Privacy scan completed')
    } catch (e) {
      setStatus(e.message)
    }
  }

  const updateFinding = async (id, patch) => {
    await api(`/privacy/findings/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    })
    await Promise.all([loadFindings(selectedDocId), loadReport(selectedDocId)])
  }

  const exportRedacted = async () => {
    if (!selectedDocId) return
    try {
      const out = await api(`/privacy/redact/${selectedDocId}`, { method: 'POST' })
      window.open(`${API}${out.download_url}`, '_blank')
      setStatus(out.message)
    } catch (e) {
      setStatus(e.message)
    }
  }

  const runConsistency = async () => {
    if (comparisonIds.length < 2) {
      setStatus('Choose at least two documents for comparison')
      return
    }
    try {
      const out = await api('/consistency/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_ids: comparisonIds, max_pairs: 30 }),
      })
      setComparisonResults(out.comparisons)
      setStatus(`Found ${out.comparisons.length} potential consistency events`)
    } catch (e) {
      setStatus(e.message)
    }
  }

  return (
    <main className="layout">
      <header>
        <h1>DocuIntellect – Enterprise AI Document Intelligence Platform</h1>
        <p>Developed by Hariom and Ayush Singh (CSE472) • Local-first processing</p>
        <div className="toolbar">
          <label className="upload">
            Upload PDF / DOCX / TXT
            <input type="file" accept=".pdf,.docx,.txt" onChange={onUpload} />
          </label>
          <span className="status">{status}</span>
        </div>
      </header>

      <section className="grid">
        <article className="card">
          <h2>Document Library</h2>
          {documents.map((doc) => (
            <button
              key={doc.id}
              className={doc.id === selectedDocId ? 'doc active' : 'doc'}
              onClick={() => setSelectedDocId(doc.id)}
            >
              <strong>{doc.filename}</strong>
              <small>
                {doc.category} • {doc.file_type.toUpperCase()}
              </small>
            </button>
          ))}
        </article>

        <article className="card wide">
          <h2>Document Understanding</h2>
          {docDetails && (
            <>
              <p><strong>Category:</strong> {docDetails.category}</p>
              <p><strong>Summary:</strong> {docDetails.summary}</p>
              <h3>Named Entities</h3>
              <div className="chips">
                {docDetails.entities.slice(0, 40).map((e, idx) => (
                  <span key={`${e.text}-${idx}`}>{e.text} ({e.label})</span>
                ))}
              </div>
            </>
          )}
        </article>

        <article className="card">
          <h2>Semantic Search</h2>
          <input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search documents..." />
          <button onClick={runSearch}>Search</button>
          {searchResults.map((r) => (
            <div key={r.chunk_id} className="result">
              <small>{r.document_name} • p.{r.page_number} • score {r.score}</small>
              <p>{r.content}</p>
            </div>
          ))}
        </article>

        <article className="card">
          <h2>Grounded QA</h2>
          <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask a question..." />
          <button onClick={runQa}>Ask</button>
          {qaResult && (
            <div className="result">
              <p><strong>Answer:</strong> {qaResult.answer}</p>
              <small>{qaResult.grounded ? 'Grounded response' : 'Insufficient evidence'}</small>
            </div>
          )}
        </article>

        <article className="card wide">
          <h2>Privacy & Sensitive Information Scanner</h2>
          <button onClick={runPrivacyScan} disabled={!selectedDoc}>Scan Selected Document</button>
          <button onClick={exportRedacted} disabled={!findings.some((f) => f.selected_for_redaction)}>
            Export Redacted Document
          </button>
          {report && (
            <p>
              Total findings: {report.total_findings} | High: {report.risk_distribution?.High || 0} | Medium:{' '}
              {report.risk_distribution?.Medium || 0} | Low: {report.risk_distribution?.Low || 0}
            </p>
          )}
          {findings.map((f) => (
            <div key={f.id} className="result">
              <p>
                <strong>{f.info_type}</strong> ({f.risk_level}) • p.{f.page_number} • {f.masked_value}
              </p>
              <small>{f.detection_method} — {f.explanation}</small>
              <div className="row">
                {['Confirmed Sensitive', 'Not Sensitive', 'Needs Review'].map((state) => (
                  <button
                    key={state}
                    onClick={() => updateFinding(f.id, { review_status: state })}
                    className={f.review_status === state ? 'active-btn' : ''}
                  >
                    {state}
                  </button>
                ))}
                <label>
                  <input
                    type="checkbox"
                    checked={f.selected_for_redaction}
                    onChange={(e) =>
                      updateFinding(f.id, {
                        review_status: f.review_status,
                        selected_for_redaction: e.target.checked,
                      })
                    }
                  />
                  Redact
                </label>
              </div>
            </div>
          ))}
        </article>

        <article className="card wide">
          <h2>Cross-Document Contradiction & Consistency Detector</h2>
          <p>Select two or more documents:</p>
          <div className="chips">
            {documents.map((doc) => (
              <label key={doc.id}>
                <input
                  type="checkbox"
                  checked={comparisonIds.includes(doc.id)}
                  onChange={(e) => {
                    setComparisonIds((prev) =>
                      e.target.checked ? [...new Set([...prev, doc.id])] : prev.filter((x) => x !== doc.id),
                    )
                  }}
                />
                {doc.filename}
              </label>
            ))}
          </div>
          <button onClick={runConsistency}>Run Comparison</button>
          {comparisonResults.map((c, idx) => (
            <div key={idx} className="result">
              <p>
                <strong>{c.relation}</strong> ({c.confidence}) — {c.reason}
              </p>
              <small>
                A: {c.statement_a.document_name} p.{c.statement_a.page_number}
              </small>
              <p>{c.statement_a.text}</p>
              <small>
                B: {c.statement_b.document_name} p.{c.statement_b.page_number}
              </small>
              <p>{c.statement_b.text}</p>
            </div>
          ))}
        </article>
      </section>
    </main>
  )
}

export default App
