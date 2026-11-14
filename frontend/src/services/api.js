const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

export const api = {
  async getHealth() {
    const res = await fetch(`${API_BASE}/api/health`);
    if (!res.ok) throw new Error("Health check failed");
    return res.json();
  },

  async listDocuments() {
    const res = await fetch(`${API_BASE}/api/documents`);
    if (!res.ok) throw new Error("Failed to load documents");
    return res.json();
  },

  async getDocuments() {
    return this.listDocuments();
  },

  async getDocument(docId) {
    const res = await fetch(`${API_BASE}/api/documents/${docId}`);
    if (!res.ok) throw new Error("Document not found");
    return res.json();
  },

  async getDocumentResults(docId) {
    const res = await fetch(`${API_BASE}/api/documents/${docId}/results`);
    if (!res.ok) throw new Error("Failed to load document analysis");
    return res.json();
  },

  async uploadDocument(file) {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${API_BASE}/api/documents/upload`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(err.detail || "Upload failed");
    }
    return res.json();
  },

  async reprocessDocument(docId) {
    const res = await fetch(`${API_BASE}/api/documents/${docId}/reprocess`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Failed to reprocess document");
    return res.json();
  },

  async deleteDocument(docId) {
    const res = await fetch(`${API_BASE}/api/documents/${docId}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete document");
    return res.json();
  },

  async summarizeDocument(docId) {
    const res = await fetch(`${API_BASE}/api/documents/${docId}/summarize`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Failed to generate summary");
    return res.json();
  },

  async askDocument(docId, question, topK = 4) {
    const res = await fetch(`${API_BASE}/api/documents/${docId}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, top_k: topK }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Error asking question" }));
      throw new Error(err.detail || "Error asking question");
    }
    return res.json();
  },

  async getChatHistory(docId) {
    const res = await fetch(`${API_BASE}/api/documents/${docId}/history`);
    if (!res.ok) throw new Error("Failed to fetch chat history");
    return res.json();
  },

  async clearChatHistory(docId) {
    const res = await fetch(`${API_BASE}/api/documents/${docId}/history`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to clear chat history");
    return res.json();
  },

  async search(query, topK = 6, documentId = null) {
    const res = await fetch(`${API_BASE}/api/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: topK, document_id: documentId }),
    });
    if (!res.ok) throw new Error("Search query failed");
    return res.json();
  },

  // Privacy & Redaction APIs
  async getPrivacyReport(docId) {
    const res = await fetch(`${API_BASE}/api/documents/${docId}/privacy`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to fetch privacy report" }));
      throw new Error(err.detail || "Failed to fetch privacy report");
    }
    return res.json();
  },

  async scanDocumentPrivacy(docId) {
    const res = await fetch(`${API_BASE}/api/documents/${docId}/privacy/scan`, {
      method: "POST",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to run privacy scan" }));
      throw new Error(err.detail || "Failed to run privacy scan");
    }
    return res.json();
  },

  async updatePrivacyFindingStatus(findingId, reviewStatus) {
    const res = await fetch(`${API_BASE}/api/privacy/findings/${findingId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ review_status: reviewStatus }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to update finding status" }));
      throw new Error(err.detail || "Failed to update finding status");
    }
    return res.json();
  },

  async redactDocument(docId, findingIds, redactionLabel = "REDACTED") {
    const res = await fetch(`${API_BASE}/api/documents/${docId}/privacy/redact`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ finding_ids: findingIds, redaction_label: redactionLabel }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Document redaction failed" }));
      throw new Error(err.detail || "Document redaction failed");
    }
    return res.json();
  },

  async getRedactionHistory(docId) {
    const res = await fetch(`${API_BASE}/api/documents/${docId}/privacy/redacted`);
    if (!res.ok) throw new Error("Failed to fetch redaction history");
    return res.json();
  },

  getRedactedDownloadUrl(redactionId) {
    return `${API_BASE}/api/privacy/download/${redactionId}`;
  },

  // Cross-Document Consistency & Contradiction APIs
  async analyzeConsistency(documentIds, minSimilarity = null, scope = "selected") {
    const res = await fetch(`${API_BASE}/api/intelligence/consistency/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        document_ids: documentIds,
        min_similarity: minSimilarity,
        scope: scope,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Consistency analysis failed" }));
      throw new Error(err.detail || "Consistency analysis failed");
    }
    return res.json();
  },

  async getConsistencyJob(analysisId) {
    const res = await fetch(`${API_BASE}/api/intelligence/consistency/${analysisId}`);
    if (!res.ok) throw new Error("Failed to fetch consistency job status");
    return res.json();
  },

  async getConflicts(filters = {}) {
    const params = new URLSearchParams();
    if (filters.analysisId) params.append("analysis_id", filters.analysisId);
    if (filters.documentId) params.append("document_id", filters.documentId);
    if (filters.conflictType) params.append("conflict_type", filters.conflictType);
    if (filters.reviewStatus) params.append("review_status", filters.reviewStatus);
    if (filters.minConfidence) params.append("min_confidence", filters.minConfidence);

    const queryStr = params.toString() ? `?${params.toString()}` : "";
    const res = await fetch(`${API_BASE}/api/intelligence/conflicts${queryStr}`);
    if (!res.ok) throw new Error("Failed to fetch conflicts");
    return res.json();
  },

  async getConflictDetail(conflictId) {
    const res = await fetch(`${API_BASE}/api/intelligence/conflicts/${conflictId}`);
    if (!res.ok) throw new Error("Failed to fetch conflict detail");
    return res.json();
  },

  async updateConflictStatus(conflictId, reviewStatus) {
    const res = await fetch(`${API_BASE}/api/intelligence/conflicts/${conflictId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ review_status: reviewStatus }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to update conflict status" }));
      throw new Error(err.detail || "Failed to update conflict status");
    }
    return res.json();
  },

  async compareDocumentsDirect(docAId, docBId, minSimilarity = null) {
    const res = await fetch(`${API_BASE}/api/intelligence/consistency/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        document_a_id: docAId,
        document_b_id: docBId,
        min_similarity: minSimilarity,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Document comparison failed" }));
      throw new Error(err.detail || "Document comparison failed");
    }
    return res.json();
  },
};

