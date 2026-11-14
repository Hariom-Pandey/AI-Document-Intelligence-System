import React, { useEffect, useState } from "react";
import {
  FileText,
  CheckCircle2,
  Clock,
  AlertTriangle,
  UploadCloud,
  ArrowRight,
  Sparkles,
  Search,
  MessageSquare,
  BarChart3,
  RefreshCw,
  AlertCircle
} from "lucide-react";
import FileUploader from "../components/FileUploader";
import { api } from "../services/api";

export default function Dashboard({ onSelectDocument, onNavigate }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadDocs = async () => {
    try {
      const data = await api.listDocuments();
      setDocuments(data);
    } catch (err) {
      console.error("Failed to load documents", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocs();
    const interval = setInterval(loadDocs, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleReprocess = async (docId) => {
    try {
      await api.reprocessDocument(docId);
      loadDocs();
    } catch (err) {
      alert("Failed to reprocess: " + err.message);
    }
  };

  const total = documents.length;
  const completed = documents.filter((d) => d.status === "completed").length;
  const processing = documents.filter((d) => d.status === "processing" || d.status === "uploaded").length;
  const failed = documents.filter((d) => d.status === "failed").length;

  // Category breakdown
  const categoryCounts = {};
  documents.forEach((d) => {
    const cat = d.category || "Unclassified";
    categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
  });

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <h2>System Dashboard</h2>
          <p className="page-sub">Overview of processed documents, AI intelligence metrics, and quick actions</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-outline" onClick={() => onNavigate("search")}>
            <Search size={16} /> Semantic Search
          </button>
          <button className="btn btn-primary" onClick={() => onNavigate("library")}>
            <UploadCloud size={16} /> Upload New
          </button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon bg-blue">
            <FileText size={22} />
          </div>
          <div>
            <span className="metric-label">Total Documents</span>
            <h3 className="metric-value">{total}</h3>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon bg-green">
            <CheckCircle2 size={22} />
          </div>
          <div>
            <span className="metric-label">Ready & Indexed</span>
            <h3 className="metric-value">{completed}</h3>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon bg-amber">
            <Clock size={22} />
          </div>
          <div>
            <span className="metric-label">Processing</span>
            <h3 className="metric-value">{processing}</h3>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon bg-red">
            <AlertTriangle size={22} />
          </div>
          <div>
            <span className="metric-label">Attention Needed</span>
            <h3 className="metric-value">{failed}</h3>
          </div>
        </div>
      </div>

      {/* Quick Upload + Category Section */}
      <div className="grid-2-col">
        {/* Quick Upload */}
        <div className="card">
          <div className="card-title-row">
            <UploadCloud size={18} className="accent-icon" />
            <h4>Quick Document Ingestion</h4>
          </div>
          <FileUploader onUploadSuccess={() => loadDocs()} />
        </div>

        {/* Document Classification Distribution */}
        <div className="card">
          <div className="card-title-row">
            <BarChart3 size={18} className="accent-icon" />
            <h4>Category Distribution</h4>
          </div>

          {Object.keys(categoryCounts).length === 0 ? (
            <div className="empty-state-sm">
              <p>No document categories registered yet.</p>
            </div>
          ) : (
            <div className="category-bars">
              {Object.entries(categoryCounts).map(([cat, count]) => {
                const pct = Math.round((count / Math.max(total, 1)) * 100);
                return (
                  <div key={cat} className="category-bar-item">
                    <div className="cat-header">
                      <span className="cat-name">{cat}</span>
                      <span className="cat-count">{count} docs ({pct}%)</span>
                    </div>
                    <div className="cat-track">
                      <div className="cat-fill" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Recent Uploads Table */}
      <div className="card">
        <div className="card-title-row">
          <Clock size={18} className="accent-icon" />
          <h4>Recent Documents</h4>
          <button className="view-all-link" onClick={() => onNavigate("library")}>
            View Library <ArrowRight size={14} />
          </button>
        </div>

        {loading ? (
          <p className="loading-text">Loading documents...</p>
        ) : documents.length === 0 ? (
          <div className="empty-table-state">
            <p>No documents uploaded yet. Upload a PDF, DOCX, or TXT file above to get started.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="doc-table">
              <thead>
                <tr>
                  <th>Filename</th>
                  <th>Category</th>
                  <th>Pages</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.slice(0, 6).map((doc) => (
                  <tr key={doc.id}>
                    <td>
                      <div className="filename-cell">
                        <FileText size={16} className="file-icon" />
                        <div>
                          <strong>{doc.filename}</strong>
                          <span className="file-ext">.{doc.file_type.toUpperCase()}</span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="category-badge">{doc.category || "General"}</span>
                    </td>
                    <td>{doc.page_count || 1} pages</td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span className={`status-badge ${doc.status}`}>
                          {doc.status}
                        </span>
                        {doc.status === "failed" && doc.error_message && (
                          <span title={doc.error_message} style={{ cursor: "pointer", color: "#f87171", display: "inline-flex" }}>
                            <AlertCircle size={14} />
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button
                          className="btn btn-outline btn-sm"
                          onClick={() => onSelectDocument(doc.id, "detail")}
                          disabled={doc.status !== "completed"}
                        >
                          <Sparkles size={14} /> Analysis
                        </button>
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => onSelectDocument(doc.id, "chat")}
                          disabled={doc.status !== "completed"}
                        >
                          <MessageSquare size={14} /> Chat
                        </button>
                        {doc.status === "failed" && (
                          <button
                            className="btn btn-outline btn-sm"
                            onClick={() => handleReprocess(doc.id)}
                            title="Retry document processing"
                          >
                            <RefreshCw size={14} /> Retry
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

