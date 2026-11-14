import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  AlertOctagon,
  Loader2,
  Lock,
  CheckSquare,
  Square,
  History,
  RefreshCw,
  FolderOpen
} from "lucide-react";
import { api } from "../services/api";
import PrivacyReport from "./PrivacyReport";
import RiskDistribution from "./RiskDistribution";
import PrivacyFindingCard from "./PrivacyFindingCard";
import RedactionPreview from "./RedactionPreview";

export default function PrivacyScanner({ documentId, filename, fileType }) {
  const [report, setReport] = useState(null);
  const [redactionHistory, setRedactionHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [updatingId, setUpdatingId] = useState(null);
  const [error, setError] = useState(null);

  // Filter States
  const [selectedRisk, setSelectedRisk] = useState("ALL");
  const [selectedCategory, setSelectedCategory] = useState("ALL");
  const [selectedStatus, setSelectedStatus] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Redaction Selection State
  const [selectedFindingIds, setSelectedFindingIds] = useState([]);
  const [showRedactionModal, setShowRedactionModal] = useState(false);

  const loadPrivacyData = async () => {
    if (!documentId) return;
    setLoading(true);
    setError(null);
    try {
      const [repData, histData] = await Promise.all([
        api.getPrivacyReport(documentId),
        api.getRedactionHistory(documentId).catch(() => [])
      ]);
      setReport(repData);
      setRedactionHistory(histData || []);
    } catch (err) {
      setError(err.message || "Failed to load privacy report.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPrivacyData();
  }, [documentId]);

  const handleRescan = async () => {
    setScanning(true);
    setError(null);
    try {
      const freshReport = await api.scanDocumentPrivacy(documentId);
      setReport(freshReport);
      setSelectedFindingIds([]);
    } catch (err) {
      setError(err.message || "Failed to re-run privacy scan.");
    } finally {
      setScanning(false);
    }
  };

  const handleUpdateStatus = async (findingId, newStatus) => {
    setUpdatingId(findingId);
    try {
      await api.updatePrivacyFindingStatus(findingId, newStatus);
      // Update local report state
      setReport((prev) => {
        if (!prev) return prev;
        const updatedFindings = prev.findings.map((f) =>
          f.id === findingId ? { ...f, review_status: newStatus } : f
        );
        return { ...prev, findings: updatedFindings };
      });
    } catch (err) {
      alert("Failed to update status: " + err.message);
    } finally {
      setUpdatingId(null);
    }
  };

  const handleToggleSelect = (findingId) => {
    setSelectedFindingIds((prev) =>
      prev.includes(findingId) ? prev.filter((id) => id !== findingId) : [...prev, findingId]
    );
  };

  const handleSelectAllHighRisk = () => {
    if (!report?.findings) return;
    const highRiskIds = report.findings
      .filter((f) => f.risk_level === "HIGH" && !f.is_redacted)
      .map((f) => f.id);
    setSelectedFindingIds(highRiskIds);
  };

  const handleSelectAllConfirmed = () => {
    if (!report?.findings) return;
    const confirmedIds = report.findings
      .filter((f) => f.review_status === "confirmed_sensitive" && !f.is_redacted)
      .map((f) => f.id);
    setSelectedFindingIds(confirmedIds);
  };

  const handleDeselectAll = () => {
    setSelectedFindingIds([]);
  };

  // Filtered Findings Calculation
  const filteredFindings = (report?.findings || []).filter((f) => {
    if (selectedRisk !== "ALL" && f.risk_level !== selectedRisk) return false;
    if (selectedCategory !== "ALL" && f.entity_type !== selectedCategory) return false;
    if (selectedStatus !== "ALL" && f.review_status !== selectedStatus) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchType = (f.entity_type || "").toLowerCase().includes(q);
      const matchValue = (f.masked_value || "").toLowerCase().includes(q);
      const matchExpl = (f.explanation || "").toLowerCase().includes(q);
      if (!matchType && !matchValue && !matchExpl) return false;
    }
    return true;
  });

  const selectedFindingsObjects = (report?.findings || []).filter((f) =>
    selectedFindingIds.includes(f.id)
  );

  return (
    <div className="privacy-scanner-container">
      {loading ? (
        <div className="privacy-loading-state">
          <Loader2 size={32} className="animate-spin text-accent" />
          <p>Performing deep privacy and sensitive information inspection...</p>
        </div>
      ) : error ? (
        <div className="alert alert-error">
          <ShieldAlert size={18} />
          <span>{error}</span>
        </div>
      ) : (
        <>
          {/* Executive Report Card */}
          <PrivacyReport
            report={report}
            onRescan={handleRescan}
            scanning={scanning}
          />

          {/* Interactive Risk & Category Filter Bar */}
          <RiskDistribution
            categoryDistribution={report?.category_distribution}
            riskSummary={report?.risk_summary}
            selectedRisk={selectedRisk}
            onSelectRisk={setSelectedRisk}
            selectedCategory={selectedCategory}
            onSelectCategory={setSelectedCategory}
            selectedStatus={selectedStatus}
            onSelectStatus={setSelectedStatus}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            totalCount={report?.total_findings || 0}
          />

          {/* Redaction Action Toolbar */}
          <div className="privacy-toolbar">
            <div className="toolbar-selection-info">
              <span>Selected for Redaction:</span>
              <strong className={selectedFindingIds.length > 0 ? "text-danger" : ""}>
                {selectedFindingIds.length} findings
              </strong>
            </div>

            <div className="toolbar-buttons">
              <button
                className="btn btn-secondary btn-sm"
                onClick={handleSelectAllHighRisk}
                title="Select all HIGH risk items (PAN, Aadhaar, Bank Details)"
              >
                Select High Risk
              </button>

              <button
                className="btn btn-secondary btn-sm"
                onClick={handleSelectAllConfirmed}
                title="Select all items you verified as confirmed sensitive"
              >
                Select Confirmed
              </button>

              {selectedFindingIds.length > 0 && (
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={handleDeselectAll}
                >
                  Clear Selection
                </button>
              )}

              <button
                className="btn btn-danger btn-sm"
                onClick={() => setShowRedactionModal(true)}
                disabled={selectedFindingIds.length === 0}
              >
                <Lock size={14} />
                <span>Redact Selected ({selectedFindingIds.length})</span>
              </button>

              {redactionHistory.length > 0 && (
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => setShowRedactionModal(true)}
                  title="View previous redacted exports"
                >
                  <History size={14} />
                  <span>History ({redactionHistory.length})</span>
                </button>
              )}
            </div>
          </div>

          {/* Findings List */}
          {filteredFindings.length === 0 ? (
            <div className="card empty-card" style={{ padding: "2.5rem" }}>
              <ShieldCheck size={40} className="text-success" style={{ margin: "0 auto 1rem" }} />
              <h4>No Findings Matching Filter</h4>
              <p className="text-muted">
                {report?.total_findings === 0
                  ? "Zero sensitive entities detected in this document."
                  : "Try resetting your search query or category filters to view other findings."}
              </p>
            </div>
          ) : (
            <div className="privacy-findings-list">
              <div className="findings-list-header">
                <span>Displaying {filteredFindings.length} of {report?.total_findings} detected item(s)</span>
              </div>
              {filteredFindings.map((finding) => (
                <PrivacyFindingCard
                  key={finding.id}
                  finding={finding}
                  isSelected={selectedFindingIds.includes(finding.id)}
                  onToggleSelect={handleToggleSelect}
                  onUpdateStatus={handleUpdateStatus}
                  updating={updatingId === finding.id}
                />
              ))}
            </div>
          )}

          {/* Redaction Modal Drawer */}
          {showRedactionModal && (
            <RedactionPreview
              documentId={documentId}
              selectedCount={selectedFindingIds.length}
              selectedFindings={selectedFindingsObjects}
              onClose={() => setShowRedactionModal(false)}
              onRedactionComplete={() => {
                loadPrivacyData();
              }}
              redactionHistory={redactionHistory}
            />
          )}
        </>
      )}
    </div>
  );
}

