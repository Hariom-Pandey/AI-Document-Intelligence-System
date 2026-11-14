import React, { useState, useEffect } from "react";
import {
  FileText,
  Trash2,
  RefreshCw,
  Sparkles,
  MessageSquare,
  AlertCircle,
  Clock,
  Filter,
  CheckCircle2,
  ExternalLink
} from "lucide-react";
import FileUploader from "../components/FileUploader";
import { api } from "../services/api";

export default function DocumentLibrary({ onSelectDocument }) {
  const [documents, setDocuments] = useState([]);
  const [filterStatus, setFilterStatus] = useState("ALL");
  const [loading, setLoading] = useState(true);
  const [actionMessage, setActionMessage] = useState(null);

  const fetchDocs = async () => {
    try {
      const data = await api.listDocuments();
      setDocuments(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
    const interval = setInterval(fetchDocs, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleDelete = async (docId, filename) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}" and its vector indices?`)) {
      return;
    }
    try {
      await api.deleteDocument(docId);
      setActionMessage(`Document "${filename}" deleted.`);
      fetchDocs();
    } catch (err) {
      alert("Failed to delete document: " + err.message);
    }
  };

  const handleReprocess = async (docId) => {
    try {
      await api.reprocessDocument(docId);
      setActionMessage("Re-processing initiated.");
      fetchDocs();
    } catch (err) {
      alert("Failed to reprocess: " + err.message);
    }
  };

  const filtered = documents.filter((d) => {
    if (filterStatus === "ALL") return true;
    return d.status.toUpperCase() === filterStatus;
  });

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <h2>Document Library & Ingestion</h2>
          <p className="page-sub">Upload, monitor, inspect, and manage your processed documents</p>
        </div>
        <button className="btn btn-outline" onClick={fetchDocs} title="Refresh list">
          <RefreshCw size={15} /> Refresh
        </button>
      </div>

      {actionMessage && (
        <div className="alert alert-success">
          <CheckCircle2 size={16} />
          <span>{actionMessage}</span>
          <button className="close-alert" onClick={() => setActionMessage(null)}>×</button>
        </div>
      )}

      {/* Upload Zone */}
      <FileUploader onUploadSuccess={() => fetchDocs()} />

      {/* Filter and Library List */}
      <div className="card">
        <div className="library-toolbar">
          <div className="toolbar-left">
            <Filter size={16} />
            <span className="toolbar-label">Filter Status:</span>
            {["ALL", "COMPLETED", "PROCESSING", "FAILED"].map((st) => (
              <button
                key={st}
                className={`tab-btn ${filterStatus === st ? "active" : ""}`}
                onClick={() => setFilterStatus(st)}
              >
                {st}
              </button>
            ))}
          </div>

          <span className="doc-count-badge">
            {filtered.length} {filtered.length === 1 ? "document" : "documents"}
          </span>
        </div>

        {loading ? (
          <p className="loading-text">Loading library...</p>
        ) : filtered.length === 0 ? (
          <div className="empty-table-state">
            <p>No documents found matching the filter.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="doc-table">
              <thead>
                <tr>
                  <th>File</th>
                  <th>Category</th>
                  <th>Pages</th>
                  <th>Size</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((doc) => (
                  <tr key={doc.id}>
                    <td>
                      <div className="filename-cell">
                        <FileText size={18} className="file-icon" />
                        <div>
                          <strong>{doc.filename}</strong>
                          <span className="doc-id-sub">ID: {doc.id.substring(0, 8)}...</span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="category-badge">{doc.category || "General"}</span>
                    </td>
                    <td>{doc.page_count || 1}</td>
                    <td>{(doc.file_size / 1024).toFixed(1)} KB</td>
                    <td>
                      <span className={`status-badge ${doc.status}`}>
                        {doc.status}
                      </span>
                      {doc.error_message && (
                        <div className="error-tooltip" title={doc.error_message}>
                          <AlertCircle size={14} className="text-danger" />
                        </div>
                      )}
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button
                          className="btn btn-outline btn-sm"
                          onClick={() => onSelectDocument(doc.id, "detail")}
                          disabled={doc.status !== "completed"}
                          title="View summary, entities and classification"
                        >
                          <Sparkles size={14} /> Analysis
                        </button>
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => onSelectDocument(doc.id, "chat")}
                          disabled={doc.status !== "completed"}
                          title="Open grounded RAG chat"
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
                        <button
                          className="btn btn-danger-outline btn-sm"
                          onClick={() => handleDelete(doc.id, doc.filename)}
                          title="Delete document and vector index"
                        >
                          <Trash2 size={14} />
                        </button>
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

