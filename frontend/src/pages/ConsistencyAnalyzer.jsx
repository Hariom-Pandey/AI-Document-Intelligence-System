import React, { useState, useEffect } from "react";
import {
  Scale,
  Play,
  RotateCw,
  AlertTriangle,
  CheckCircle,
  FileSearch,
  Filter,
  CheckCheck
} from "lucide-react";
import { api } from "../services/api";
import DocumentComparisonSelector from "../components/DocumentComparisonSelector";
import ConsistencyDashboard from "../components/ConsistencyDashboard";
import ConsistencyFilters from "../components/ConsistencyFilters";
import ConflictCard from "../components/ConflictCard";

export default function ConsistencyAnalyzer({ onSelectDocument, onNavigate }) {
  const [documents, setDocuments] = useState([]);
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState(null);

  // Analysis result state
  const [report, setReport] = useState(null);
  const [conflicts, setConflicts] = useState([]);

  // Filter states
  const [activeCategory, setActiveCategory] = useState("ALL");
  const [activeStatus, setActiveStatus] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Load uploaded documents on mount
  useEffect(() => {
    loadDocuments();
    loadPastConflicts();
  }, []);

  const loadDocuments = async () => {
    try {
      setLoadingDocs(true);
      const docs = await api.listDocuments();
      // Filter completed documents with extracted text
      const validDocs = (docs || []).filter((d) => d.status === "completed");
      setDocuments(validDocs);

      // Default select first 2 documents if available and none selected
      setSelectedDocIds((prev) => {
        if (prev.length === 0 && validDocs.length >= 2) {
          return [validDocs[0].id, validDocs[1].id];
        }
        return prev;
      });
    } catch (err) {
      console.error("Failed to load documents for consistency:", err);
    } finally {
      setLoadingDocs(false);
    }
  };

  const loadPastConflicts = async () => {
    try {
      const saved = await api.getConflicts();
      if (saved && saved.length > 0) {
        setConflicts(saved);
      }
    } catch (err) {
      console.error("Failed to load saved conflicts:", err);
    }
  };

  const handleToggleDoc = (docId) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  const handleSelectAll = () => {
    setSelectedDocIds(documents.map((d) => d.id));
  };

  const handleClearAll = () => {
    setSelectedDocIds([]);
  };

  const handleRunAnalysis = async () => {
    if (selectedDocIds.length < 2) return;
    setAnalyzing(true);
    setAnalysisError(null);

    try {
      const result = await api.analyzeConsistency(selectedDocIds);
      if (result && result.report) {
        setReport(result.report);
        setConflicts(result.report.findings || []);
      }
    } catch (err) {
      console.error("Consistency analysis failed:", err);
      setAnalysisError(err.message || "Failed to analyze document consistency.");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleStatusChange = async (conflictId, newStatus) => {
    try {
      await api.updateConflictStatus(conflictId, newStatus);
      // Update local state
      setConflicts((prev) =>
        prev.map((c) => (c.id === conflictId ? { ...c, review_status: newStatus } : c))
      );
    } catch (err) {
      console.error("Failed to update status:", err);
    }
  };

  // Derive categories present in findings
  const availableCategories = Array.from(
    new Set(conflicts.map((c) => c.conflict_type).filter(Boolean))
  );

  // Filtered conflicts
  const filteredConflicts = conflicts.filter((c) => {
    if (activeCategory !== "ALL" && c.conflict_type !== activeCategory) {
      return false;
    }
    if (activeStatus !== "ALL" && c.review_status !== activeStatus) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchA = c.statement_a?.toLowerCase().includes(q);
      const matchB = c.statement_b?.toLowerCase().includes(q);
      const matchDocA = c.document_a_name?.toLowerCase().includes(q);
      const matchDocB = c.document_b_name?.toLowerCase().includes(q);
      const matchExp = c.explanation?.toLowerCase().includes(q);
      if (!matchA && !matchB && !matchDocA && !matchDocB && !matchExp) {
        return false;
      }
    }
    return true;
  });

  return (
    <div className="consistency-page-container">
      {/* Page Title & Mission Header */}
      <div className="page-header-row">
        <div>
          <h2 className="page-main-title">
            <Scale size={24} className="title-icon" />
            <span>Cross-Document Contradiction & Consistency Detector</span>
          </h2>
          <p className="page-main-subtitle">
            Detect conflicting project budgets, conflicting calendar dates, incompatible contractual terms,
            and factual contradictions across your multi-document corpus using local NLI and semantic analysis.
          </p>
        </div>

        <button
          type="button"
          className="btn-primary-action run-analysis-btn"
          disabled={selectedDocIds.length < 2 || analyzing}
          onClick={handleRunAnalysis}
        >
          {analyzing ? (
            <>
              <RotateCw size={16} className="spin-icon" />
              <span>Analyzing Documents...</span>
            </>
          ) : (
            <>
              <Play size={16} />
              <span>Analyze Consistency ({selectedDocIds.length})</span>
            </>
          )}
        </button>
      </div>

      {analysisError && (
        <div className="error-banner">
          <AlertTriangle size={18} />
          <span>{analysisError}</span>
        </div>
      )}

      {/* Document Selector Section */}
      <DocumentComparisonSelector
        documents={documents}
        selectedDocIds={selectedDocIds}
        onToggleDoc={handleToggleDoc}
        onSelectAll={handleSelectAll}
        onClearAll={handleClearAll}
        onReload={loadDocuments}
        onNavigate={onNavigate}
        loading={loadingDocs}
        disabled={analyzing}
      />

      {/* Consistency Executive Dashboard */}
      {report && (
        <ConsistencyDashboard
          totalPairs={report.total_pairs_analyzed}
          totalConflicts={report.total_conflicts}
          highConfidenceCount={report.high_confidence_count}
          uncertainCount={report.uncertain_count}
          categoriesDistribution={report.categories_distribution}
          documentCount={selectedDocIds.length}
        />
      )}

      {/* Filter and Search Bar */}
      {conflicts.length > 0 && (
        <ConsistencyFilters
          activeCategory={activeCategory}
          onCategoryChange={setActiveCategory}
          activeStatus={activeStatus}
          onStatusChange={setActiveStatus}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          categories={availableCategories}
        />
      )}

      {/* Findings Section */}
      <div className="conflicts-list-section">
        <div className="section-header-row">
          <h3 className="section-title">
            <span>Detected Conflicts & Discrepancies</span>
            <span className="count-pill">{filteredConflicts.length}</span>
          </h3>

          {conflicts.length > 0 && (
            <span className="results-meta">
              Showing {filteredConflicts.length} of {conflicts.length} findings
            </span>
          )}
        </div>

        {analyzing ? (
          <div className="analyzing-state-box">
            <RotateCw size={32} className="spin-icon text-cyan" />
            <h4>Running Multi-Document Cross-Analysis</h4>
            <p>
              Extracting statements, generating candidate semantic embeddings, and performing NLI contradiction checks...
            </p>
          </div>
        ) : filteredConflicts.length > 0 ? (
          <div className="conflicts-grid">
            {filteredConflicts.map((conflict) => (
              <ConflictCard
                key={conflict.id || `${conflict.document_a_id}-${conflict.document_b_id}-${conflict.statement_a.slice(0, 15)}`}
                conflict={conflict}
                onStatusChange={handleStatusChange}
              />
            ))}
          </div>
        ) : conflicts.length > 0 ? (
          <div className="empty-state-box">
            <Filter size={32} className="empty-icon" />
            <h4>No Matching Conflicts</h4>
            <p>No findings match your current category, status, or search filters.</p>
          </div>
        ) : (
          <div className="empty-state-box">
            <CheckCheck size={36} className="empty-icon-success" />
            <h4>No Conflicts Detected</h4>
            <p>
              Select 2 or more documents above and click <strong>"Analyze Consistency"</strong> to audit statements
              for contradictions, financial figures, and deadline mismatches.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

