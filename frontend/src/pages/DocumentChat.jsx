import React, { useState, useEffect } from "react";
import { MessageSquare, FileText, ChevronDown, Sparkles, FolderOpen } from "lucide-react";
import ChatPanel from "../components/ChatPanel";
import { api } from "../services/api";

export default function DocumentChat({ initialDocId }) {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(initialDocId || "");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listDocuments()
      .then((docs) => {
        const ready = docs.filter((d) => d.status === "completed");
        setDocuments(ready);
        if (!selectedDocId && ready.length > 0) {
          setSelectedDocId(ready[0].id);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  const selectedDoc = documents.find((d) => d.id === selectedDocId);

  return (
    <div className="page-content chat-page-layout">
      {/* Document Selector Header */}
      <div className="chat-selector-banner">
        <div className="selector-info">
          <MessageSquare size={20} className="accent-icon" />
          <span>Active Context:</span>
          {documents.length > 0 ? (
            <select
              className="doc-select-input"
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename} ({d.category || "General"})
                </option>
              ))}
            </select>
          ) : (
            <span className="no-docs-text">No completed documents available.</span>
          )}
        </div>

        {selectedDoc && (
          <div className="selected-meta-chips">
            <span className="chip-sm">{selectedDoc.category || "General"}</span>
            <span className="chip-sm">{selectedDoc.page_count} pages</span>
          </div>
        )}
      </div>

      {/* Main Chat Interface */}
      {selectedDocId ? (
        <ChatPanel
          key={selectedDocId}
          documentId={selectedDocId}
          documentTitle={selectedDoc?.filename}
          category={selectedDoc?.category}
        />
      ) : (
        <div className="card empty-card" style={{ marginTop: "2rem" }}>
          <FolderOpen size={36} className="muted-icon" />
          <h3>No Document Ready for Chat</h3>
          <p>Upload and process a document in the library before initiating grounded RAG conversations.</p>
        </div>
      )}
    </div>
  );
}

