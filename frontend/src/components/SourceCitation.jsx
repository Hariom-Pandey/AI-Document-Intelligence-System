import React, { useState } from "react";
import { BookOpen, ChevronDown, ChevronUp, FileText, CheckCircle2 } from "lucide-react";

export default function SourceCitation({ citation, index }) {
  const [expanded, setExpanded] = useState(false);
  const scorePercent = Math.min(100, Math.max(0, Math.round((citation.score || 0) * 100)));

  return (
    <div className="citation-card">
      <div className="citation-header" onClick={() => setExpanded(!expanded)}>
        <div className="citation-title">
          <BookOpen size={16} className="citation-icon" />
          <span className="citation-badge">Source {index + 1}</span>
          <span className="citation-page">Page {citation.page_number || 1}</span>
        </div>

        <div className="citation-meta">
          <div className="citation-score">
            <span>Match: {scorePercent}%</span>
            <div className="score-bar-bg">
              <div className="score-bar-fill" style={{ width: `${scorePercent}%` }} />
            </div>
          </div>
          <button className="expand-btn" type="button" aria-label="Toggle snippet">
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="citation-body">
          <div className="citation-snippet">
            <span className="snippet-quote">“</span>
            {citation.snippet}
            <span className="snippet-quote">”</span>
          </div>
          <div className="citation-footer">
            <span className="chunk-tag">Chunk #{citation.chunk_index}</span>
            <span className="verified-tag">
              <CheckCircle2 size={12} /> Grounded Evidence
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

