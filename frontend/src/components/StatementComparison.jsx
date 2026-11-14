import React from "react";
import { FileText, ArrowRightLeft } from "lucide-react";

export default function StatementComparison({
  statementA,
  statementB,
  documentAName,
  documentBName,
  pageA,
  pageB,
  highlightTerms = []
}) {
  const renderHighlightedText = (text, terms) => {
    if (!terms || terms.length === 0) return text;

    // Build regex to match terms or numbers
    const validTerms = terms
      .filter((t) => typeof t === "string" && t.trim().length > 1)
      .map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));

    if (validTerms.length === 0) return text;

    const pattern = new RegExp(`(${validTerms.join("|")})`, "gi");
    const parts = text.split(pattern);

    return parts.map((part, i) => {
      const isMatch = validTerms.some((t) => t.toLowerCase() === part.toLowerCase());
      return isMatch ? (
        <mark key={i} className="statement-highlight">
          {part}
        </mark>
      ) : (
        <span key={i}>{part}</span>
      );
    });
  };

  return (
    <div className="statement-comparison-grid">
      {/* Document A Column */}
      <div className="statement-box statement-box-a">
        <div className="statement-header">
          <div className="doc-meta-badge">
            <FileText size={14} className="doc-icon-a" />
            <span className="doc-title" title={documentAName}>
              {documentAName}
            </span>
          </div>
          <span className="page-pill">Page {pageA || 1}</span>
        </div>
        <div className="statement-body">
          <p className="statement-text">
            {renderHighlightedText(statementA, highlightTerms)}
          </p>
        </div>
      </div>

      {/* Comparison Divider Icon */}
      <div className="statement-divider">
        <div className="divider-icon">
          <ArrowRightLeft size={16} />
        </div>
      </div>

      {/* Document B Column */}
      <div className="statement-box statement-box-b">
        <div className="statement-header">
          <div className="doc-meta-badge">
            <FileText size={14} className="doc-icon-b" />
            <span className="doc-title" title={documentBName}>
              {documentBName}
            </span>
          </div>
          <span className="page-pill">Page {pageB || 1}</span>
        </div>
        <div className="statement-body">
          <p className="statement-text">
            {renderHighlightedText(statementB, highlightTerms)}
          </p>
        </div>
      </div>
    </div>
  );
}

