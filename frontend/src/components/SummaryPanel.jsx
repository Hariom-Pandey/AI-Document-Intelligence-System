import React, { useState } from "react";
import { Sparkles, RefreshCw, CheckCircle2, AlignLeft, ListOrdered, ChevronRight } from "lucide-react";
import { api } from "../services/api";

export default function SummaryPanel({ documentId, summary, onSummaryUpdated }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleRegenerate = async () => {
    if (!documentId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.summarizeDocument(documentId);
      if (onSummaryUpdated) onSummaryUpdated(res);
    } catch (err) {
      setError(err.message || "Failed to regenerate summary.");
    } finally {
      setLoading(false);
    }
  };

  if (!summary) {
    return (
      <div className="card empty-card">
        <Sparkles size={32} className="muted-icon" />
        <p>No summary generated yet. The document might still be processing.</p>
        {documentId && (
          <button className="btn btn-outline" onClick={handleRegenerate} disabled={loading}>
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Generate Summary
          </button>
        )}
      </div>
    );
  }

  // Parses section headings, bold labels, and bullet items
  const renderDetailedBlock = (block, blockIdx) => {
    const rawLines = block.split(/\r?\n/).filter((l) => l.trim().length > 0);
    if (!rawLines.length) return null;

    let heading = null;
    let contentLines = rawLines;

    // Detect section header: ends with colon and doesn't start with bullet
    if (rawLines[0].trim().endsWith(":") && !rawLines[0].trim().startsWith("•") && !rawLines[0].trim().startsWith("-")) {
      heading = rawLines[0].trim();
      contentLines = rawLines.slice(1);
    }

    return (
      <div key={blockIdx} className="detailed-section-block">
        {heading && (
          <h5 className="detailed-section-title">
            <ChevronRight size={15} className="title-chevron" />
            <span>{heading}</span>
          </h5>
        )}

        <div className="section-body">
          {contentLines.map((line, lineIdx) => {
            const trimmed = line.trim();
            const isSubBullet = line.startsWith("  -") || line.startsWith("    -") || line.startsWith("\t-");
            const isBullet = trimmed.startsWith("•") || trimmed.startsWith("*") || (trimmed.startsWith("-") && !isSubBullet);

            if (isBullet || isSubBullet) {
              const cleanText = trimmed.replace(/^[•\*\-]\s*/, "");
              const cIdx = cleanText.indexOf(":");
              let label = null;
              let rest = cleanText;

              if (cIdx > 0 && cIdx < 45 && !cleanText.slice(0, cIdx).includes("http")) {
                label = cleanText.slice(0, cIdx);
                rest = cleanText.slice(cIdx + 1);
              }

              return (
                <div
                  key={lineIdx}
                  className={`detailed-bullet-item ${isSubBullet ? "sub-bullet" : ""}`}
                >
                  <span className="bullet-dot">{isSubBullet ? "–" : "•"}</span>
                  <div className="bullet-content">
                    {label ? (
                      <>
                        <strong className="bullet-label">{label}:</strong>
                        <span>{rest}</span>
                      </>
                    ) : (
                      <span>{cleanText}</span>
                    )}
                  </div>
                </div>
              );
            }

            return (
              <p key={lineIdx} className="detailed-paragraph">
                {line}
              </p>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="summary-container">
      <div className="card-header-row">
        <div className="section-title">
          <Sparkles size={20} className="accent-icon" />
          <h3>AI Document Summary</h3>
        </div>
        <button
          className="btn btn-outline btn-sm"
          onClick={handleRegenerate}
          disabled={loading}
          title="Regenerate summary with latest model parameters"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          {loading ? "Regenerating..." : "Regenerate"}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Executive Summary */}
      <div className="summary-highlight-card">
        <div className="highlight-tag">
          <Sparkles size={14} /> Executive Summary
        </div>
        <p className="highlight-text">{summary.short_summary}</p>
      </div>

      {/* Relevant Key Takeaways */}
      {summary.key_points && summary.key_points.length > 0 && (
        <div className="card key-points-card">
          <h4>
            <ListOrdered size={16} /> Key Takeaways & Core Insights
          </h4>
          <ul className="points-list">
            {summary.key_points.map((pt, i) => {
              const colonIdx = pt.indexOf(":");
              let label = null;
              let rest = pt;
              if (colonIdx > 0 && colonIdx < 45) {
                label = pt.slice(0, colonIdx);
                rest = pt.slice(colonIdx + 1);
              }
              return (
                <li key={i} className="point-item">
                  <CheckCircle2 size={16} className="point-icon" />
                  <span>
                    {label ? (
                      <>
                        <strong className="point-label">{label}:</strong>{rest}
                      </>
                    ) : (
                      pt
                    )}
                  </span>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {/* Detailed Overview */}
      <div className="card summary-detail-card">
        <h4>
          <AlignLeft size={16} /> Detailed Overview
        </h4>
        <div className="detailed-content">
          {summary.detailed_summary.split(/\n\n+/).map((block, idx) =>
            renderDetailedBlock(block, idx)
          )}
        </div>
      </div>
    </div>
  );
}
