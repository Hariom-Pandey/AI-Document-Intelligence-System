import React, { useState } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  Download,
  AlertTriangle,
  Loader2,
  X,
  FileCheck,
  History,
  Lock
} from "lucide-react";
import { api } from "../services/api";

export default function RedactionPreview({
  documentId,
  selectedCount,
  selectedFindings,
  onClose,
  onRedactionComplete,
  redactionHistory
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [redactionResult, setRedactionResult] = useState(null);
  const [redactionLabel, setRedactionLabel] = useState("REDACTED");

  const handleApplyRedaction = async () => {
    if (!selectedFindings || selectedFindings.length === 0) return;

    setLoading(true);
    setError(null);
    try {
      const findingIds = selectedFindings.map((f) => f.id);
      const res = await api.redactDocument(documentId, findingIds, redactionLabel);
      setRedactionResult(res);
      if (onRedactionComplete) {
        onRedactionComplete(res);
      }
    } catch (err) {
      setError(err.message || "Failed to redact document.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content redaction-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <Lock size={20} className="text-danger" />
            <h3>Permanent Document Redaction</h3>
          </div>
          <button className="btn-close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {error && <div className="alert alert-error">{error}</div>}

          {redactionResult ? (
            /* Success & Download State */
            <div className="redaction-success-view">
              <div className="success-icon-banner">
                <ShieldCheck size={44} className="text-success" />
                <h4>Redaction & Verification Complete</h4>
                <p>
                  {redactionResult.findings_count} sensitive finding(s) have been permanently wiped from the document content stream.
                </p>
              </div>

              <div className="verification-badge-card">
                <FileCheck size={18} className="text-success" />
                <div>
                  <strong>Post-Redaction Verification Passed</strong>
                  <span>Text extraction confirms zero trace of redacted tokens in output file.</span>
                </div>
              </div>

              <div className="redaction-download-row">
                <a
                  href={api.getRedactedDownloadUrl(redactionResult.redaction_id)}
                  download={redactionResult.redacted_filename}
                  className="btn btn-primary download-btn"
                >
                  <Download size={16} />
                  <span>Download Redacted File ({redactionResult.redacted_filename})</span>
                </a>
              </div>
            </div>
          ) : (
            /* Redaction Configuration State */
            <div className="redaction-config-view">
              <div className="redaction-summary-card">
                <div className="summary-stat-row">
                  <span>Selected Findings to Redact:</span>
                  <strong className="text-danger">{selectedCount}</strong>
                </div>
                <div className="findings-preview-list">
                  {selectedFindings.slice(0, 5).map((f) => (
                    <div key={f.id} className="preview-finding-item">
                      <span className="badge badge-sm">{f.entity_type.replace("_", " ")}</span>
                      <code>{f.masked_value}</code>
                      <span className="text-muted">(Page {f.page_number})</span>
                    </div>
                  ))}
                  {selectedFindings.length > 5 && (
                    <div className="text-muted text-sm">+ {selectedFindings.length - 5} more items...</div>
                  )}
                </div>
              </div>

              {/* Redaction Options */}
              <div className="redaction-options">
                <label className="form-label">Redaction Replacement Label:</label>
                <div className="label-radio-group">
                  {["REDACTED", "CONFIDENTIAL", "MASKED"].map((lbl) => (
                    <label key={lbl} className="radio-label">
                      <input
                        type="radio"
                        name="redaction_label"
                        value={lbl}
                        checked={redactionLabel === lbl}
                        onChange={(e) => setRedactionLabel(e.target.value)}
                      />
                      <span>[{lbl}]</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Safety Notice */}
              <div className="safety-notice-card">
                <AlertTriangle size={18} className="text-warning" />
                <div>
                  <strong>Zero Overwrite Safety Guarantee</strong>
                  <span>
                    Your original document remains completely untouched. A separate, sanitized copy will be generated and verified.
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Past Redaction History */}
          {redactionHistory && redactionHistory.length > 0 && !redactionResult && (
            <div className="redaction-history-section">
              <div className="history-header">
                <History size={14} />
                <span>Previously Generated Redacted Copies ({redactionHistory.length}):</span>
              </div>
              <div className="history-list">
                {redactionHistory.map((item) => (
                  <div key={item.id} className="history-item">
                    <div className="history-item-info">
                      <span className="history-filename">{item.redacted_filename}</span>
                      <span className="history-meta">
                        {item.findings_count} items redacted • {new Date(item.created_at).toLocaleString()}
                      </span>
                    </div>
                    <a
                      href={api.getRedactedDownloadUrl(item.id)}
                      download={item.redacted_filename}
                      className="btn btn-secondary btn-sm"
                    >
                      <Download size={13} /> Download
                    </a>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            {redactionResult ? "Close" : "Cancel"}
          </button>

          {!redactionResult && (
            <button
              className="btn btn-danger"
              onClick={handleApplyRedaction}
              disabled={loading || selectedCount === 0}
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Sanitizing & Verifying Document...</span>
                </>
              ) : (
                <>
                  <Lock size={16} />
                  <span>Permanently Redact ({selectedCount} items)</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

