import React, { useState, useEffect } from "react";
import { Search, Sparkles, FileText, ArrowRight, BookOpen, Filter, MessageSquare, Loader2 } from "lucide-react";
import { api } from "../services/api";

export default function SearchPage({ onSelectDocument }) {
  const [query, setQuery] = useState("");
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState("");
  const [topK, setTopK] = useState(6);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.listDocuments()
      .then((docs) => setDocuments(docs.filter((d) => d.status === "completed")))
      .catch(console.error);
  }, []);

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setSearched(true);

    try {
      const res = await api.search(
        query.trim(),
        topK,
        selectedDocId ? selectedDocId : null
      );
      setResults(res.results || []);
    } catch (err) {
      setError(err.message || "Semantic search failed.");
    } finally {
      setLoading(false);
    }
  };

  const sampleSearches = [
    "confidentiality and non-disclosure obligations",
    "quarterly financial revenues and cash flows",
    "system architecture and API endpoints",
    "termination penalties and liabilities",
  ];

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <h2>Semantic Passage Search</h2>
          <p className="page-sub">
            Find relevant paragraphs across documents by meaning using Sentence Transformers and FAISS
          </p>
        </div>
      </div>

      {/* Search Input Card */}
      <div className="card search-box-card">
        <form onSubmit={handleSearch} className="search-form">
          <div className="search-input-wrapper">
            <Search size={20} className="search-field-icon" />
            <input
              type="text"
              placeholder="Search concepts, questions, terms, or clauses (e.g., 'breach of agreement penalties')..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="search-main-input"
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !query.trim()}
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
              <span>Search</span>
            </button>
          </div>

          <div className="search-filters-row">
            <div className="filter-group">
              <Filter size={14} />
              <label>Filter Document:</label>
              <select
                value={selectedDocId}
                onChange={(e) => setSelectedDocId(e.target.value)}
                className="filter-select"
              >
                <option value="">All Indexed Documents</option>
                {documents.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.filename}
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label>Top Results:</label>
              <select
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="filter-select-sm"
              >
                <option value={3}>3</option>
                <option value={5}>5</option>
                <option value={8}>8</option>
                <option value={12}>12</option>
              </select>
            </div>
          </div>
        </form>

        {/* Suggested Searches */}
        {!searched && (
          <div className="search-suggestions">
            <span className="suggestion-label">Suggested Queries:</span>
            <div className="suggestion-pills">
              {sampleSearches.map((s, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="prompt-pill"
                  onClick={() => {
                    setQuery(s);
                  }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Results Section */}
      {searched && (
        <div className="search-results-section">
          <div className="results-header">
            <h4>
              Found {results.length} relevant passage{results.length === 1 ? "" : "s"} for "{query}"
            </h4>
          </div>

          {results.length === 0 ? (
            <div className="card empty-card">
              <BookOpen size={36} className="muted-icon" />
              <h3>No Matches Found</h3>
              <p>Try modifying your query or lowering the similarity constraint.</p>
            </div>
          ) : (
            <div className="results-list">
              {results.map((res, index) => {
                const scorePct = Math.round((res.score || 0) * 100);
                return (
                  <div key={index} className="card result-card">
                    <div className="result-card-header">
                      <div className="result-doc-info">
                        <FileText size={16} className="accent-icon" />
                        <strong>{res.filename}</strong>
                        <span className="category-badge">{res.category || "General"}</span>
                        <span className="page-pill">Page {res.page_number}</span>
                      </div>

                      <div className="result-score-badge">
                        <span>{scorePct}% Semantic Match</span>
                        <div className="score-bar-bg">
                          <div className="score-bar-fill" style={{ width: `${scorePct}%` }} />
                        </div>
                      </div>
                    </div>

                    <div className="result-passage">
                      <p>{res.snippet}</p>
                    </div>

                    <div className="result-card-footer">
                      <span className="chunk-tag">Passage #{res.chunk_index}</span>
                      <div className="result-actions">
                        <button
                          className="btn btn-outline btn-sm"
                          onClick={() => onSelectDocument(res.document_id, "detail")}
                        >
                          <Sparkles size={13} /> View Analysis
                        </button>
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => onSelectDocument(res.document_id, "chat")}
                        >
                          <MessageSquare size={13} /> Chat with Document
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

