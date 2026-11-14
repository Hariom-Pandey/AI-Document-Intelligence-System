import React, { useState, useEffect } from "react";
import {
  ArrowLeft,
  FileText,
  Sparkles,
  Tag,
  MessageSquare,
  AlignLeft,
  Calendar,
  Layers,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  FolderOpen,
  ShieldAlert
} from "lucide-react";
import SummaryPanel from "../components/SummaryPanel";
import EntityPanel from "../components/EntityPanel";
import ChatPanel from "../components/ChatPanel";
import PrivacyScanner from "../components/PrivacyScanner";
import { api } from "../services/api";

export default function DocumentDetail({ documentId, onBack, onNavigateChat }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("summary");

  const loadResults = async () => {
    if (!documentId) return;
    try {
      setLoading(true);
      const res = await api.getDocumentResults(documentId);
      setData(res);
    } catch (err) {
      setError(err.message || "Failed to load document analysis.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadResults();
  }, [documentId]);

  if (loading) {
    return (
      <div className="page-content loading-screen">
        <RefreshCw size={28} className="animate-spin accent-icon" />
        <p>Loading document intelligence analysis...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="page-content">
        <button className="btn btn-outline" onClick={onBack}>
          <ArrowLeft size={16} /> Back to Library
        </button>
        <div className="alert alert-error" style={{ marginTop: "1rem" }}>
          {error || "Document not found."}
        </div>
      </div>
    );
  }

  const { document, summary, classification, entities, chunks_count } = data;
  const confidencePercent = Math.round((classification?.confidence || 0) * 100);

  return (
    <div className="page-content">
      {/* Top Navigation */}
      <div className="detail-top-bar">
        <button className="btn btn-outline btn-sm" onClick={onBack}>
          <ArrowLeft size={16} /> Back
        </button>
        <div className="detail-actions">
          <button
            className="btn btn-primary btn-sm"
            onClick={() => onNavigateChat(document.id)}
          >
            <MessageSquare size={16} /> Open Full Chat
          </button>
        </div>
      </div>

      {/* Document Header Card */}
      <div className="card doc-header-card">
        <div className="doc-header-main">
          <div className="doc-badge-large">
            <FileText size={32} />
          </div>
          <div>
            <div className="doc-title-row">
              <h2>{document.filename}</h2>
              <span className={`status-badge ${document.status}`}>{document.status}</span>
            </div>
            <div className="doc-meta-row">
              <span><strong>Category:</strong> {classification?.category || "General"}</span>
              <span>•</span>
              <span><strong>Pages:</strong> {document.page_count}</span>
              <span>•</span>
              <span><strong>Size:</strong> {(document.file_size / 1024).toFixed(1)} KB</span>
              <span>•</span>
              <span><strong>Chunks:</strong> {chunks_count} passages</span>
              <span>•</span>
              <span><strong>Uploaded:</strong> {new Date(document.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        {/* Classification Confidence Widget */}
        {classification && (
          <div className="classification-widget">
            <div className="clf-title">
              <span>Predicted Category</span>
              <span className="clf-conf">{confidencePercent}% match</span>
            </div>
            <div className="clf-name">{classification.category}</div>
            <div className="clf-bar-bg">
              <div className="clf-bar-fill" style={{ width: `${confidencePercent}%` }} />
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="detail-tabs">
        <button
          className={`detail-tab ${activeTab === "summary" ? "active" : ""}`}
          onClick={() => setActiveTab("summary")}
        >
          <Sparkles size={16} /> Summary & Insights
        </button>
        <button
          className={`detail-tab ${activeTab === "entities" ? "active" : ""}`}
          onClick={() => setActiveTab("entities")}
        >
          <Tag size={16} /> Extracted Entities ({entities.length})
        </button>
        <button
          className={`detail-tab ${activeTab === "chat" ? "active" : ""}`}
          onClick={() => setActiveTab("chat")}
        >
          <MessageSquare size={16} /> Grounded Q&A
        </button>
        <button
          className={`detail-tab ${activeTab === "privacy" ? "active" : ""}`}
          onClick={() => setActiveTab("privacy")}
        >
          <ShieldAlert size={16} /> Privacy & Security
        </button>
        <button
          className={`detail-tab ${activeTab === "text" ? "active" : ""}`}
          onClick={() => setActiveTab("text")}
        >
          <AlignLeft size={16} /> Extracted Text
        </button>
      </div>

      {/* Tab Panels */}
      <div className="detail-tab-body">
        {activeTab === "summary" && (
          <SummaryPanel
            documentId={document.id}
            summary={summary}
            onSummaryUpdated={() => loadResults()}
          />
        )}

        {activeTab === "entities" && (
          <EntityPanel entities={entities} />
        )}

        {activeTab === "chat" && (
          <ChatPanel
            documentId={document.id}
            documentTitle={document.filename}
            category={document.category}
          />
        )}

        {activeTab === "privacy" && (
          <PrivacyScanner
            documentId={document.id}
            filename={document.filename}
            fileType={document.file_type}
          />
        )}

        {activeTab === "text" && (
          <div className="card text-preview-card">
            <div className="card-title-row">
              <AlignLeft size={18} className="accent-icon" />
              <h4>Extracted Document Content ({document.page_count} pages)</h4>
            </div>
            <div className="raw-text-viewer">
              <pre>{document.extracted_text_preview || "No text available."}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

