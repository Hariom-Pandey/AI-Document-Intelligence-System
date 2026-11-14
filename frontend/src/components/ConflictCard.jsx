import React, { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Calendar,
  DollarSign,
  Scale,
  Briefcase,
  Users,
  GitBranch,
  HelpCircle,
  FileText
} from "lucide-react";
import StatementComparison from "./StatementComparison";
import ConflictEvidence from "./ConflictEvidence";
import ReviewStatus from "./ReviewStatus";

export default function ConflictCard({ conflict, onStatusChange }) {
  const [expanded, setExpanded] = useState(false);

  const categoryMeta = {
    NUMERICAL_INCONSISTENCY: {
      label: "Numerical Inconsistency",
      icon: <DollarSign size={14} />,
      colorClass: "cat-amber"
    },
    DATE_INCONSISTENCY: {
      label: "Date Inconsistency",
      icon: <Calendar size={14} />,
      colorClass: "cat-orange"
    },
    FACTUAL_CONTRADICTION: {
      label: "Factual Contradiction",
      icon: <AlertCircle size={14} />,
      colorClass: "cat-red"
    },
    CONTRACTUAL_CONFLICT: {
      label: "Contractual Conflict",
      icon: <Scale size={14} />,
      colorClass: "cat-purple"
    },
    RESPONSIBILITY_CONFLICT: {
      label: "Responsibility Conflict",
      icon: <Briefcase size={14} />,
      colorClass: "cat-indigo"
    },
    ENTITY_INCONSISTENCY: {
      label: "Entity Inconsistency",
      icon: <Users size={14} />,
      colorClass: "cat-cyan"
    },
    POTENTIAL_VERSION_CHANGE: {
      label: "Potential Version Change",
      icon: <GitBranch size={14} />,
      colorClass: "cat-teal"
    },
    UNRESOLVED_DIFFERENCE: {
      label: "Unresolved Difference",
      icon: <HelpCircle size={14} />,
      colorClass: "cat-slate"
    }
  };

  const meta = categoryMeta[conflict.conflict_type] || categoryMeta.UNRESOLVED_DIFFERENCE;

  // Extract highlight terms from evidence context (values, dates, subject)
  const highlightTerms = [
    conflict.evidence_context?.value_a,
    conflict.evidence_context?.value_b,
    conflict.evidence_context?.date_a,
    conflict.evidence_context?.date_b,
    conflict.evidence_context?.subject
  ].filter(Boolean);

  return (
    <div className={`conflict-card ${meta.colorClass}`}>
      {/* Top Header Row */}
      <div className="conflict-card-header">
        <div className="header-left">
          <div className="conflict-category-badge">
            {meta.icon}
            <span>{meta.label}</span>
          </div>

          <span className="confidence-pill">
            {Math.round((conflict.confidence || 0) * 100)}% Confidence
          </span>
        </div>

        <div className="header-right">
          <ReviewStatus
            currentStatus={conflict.review_status}
            onStatusChange={(newStatus) => onStatusChange(conflict.id, newStatus)}
          />

          <button
            type="button"
            className="expand-btn"
            onClick={() => setExpanded(!expanded)}
            title={expanded ? "Collapse evidence" : "Expand evidence"}
          >
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </div>

      {/* Main Statement Side-by-Side Comparison */}
      <div className="conflict-card-body">
        <StatementComparison
          statementA={conflict.statement_a}
          statementB={conflict.statement_b}
          documentAName={conflict.document_a_name || "Document A"}
          documentBName={conflict.document_b_name || "Document B"}
          pageA={conflict.page_a}
          pageB={conflict.page_b}
          highlightTerms={highlightTerms}
        />
      </div>

      {/* Expandable Explanation & Evidence Matrix */}
      {expanded && (
        <div className="conflict-card-footer">
          <ConflictEvidence
            explanation={conflict.explanation}
            evidenceContext={conflict.evidence_context}
            confidence={conflict.confidence}
            nliLabel={conflict.nli_label}
          />
        </div>
      )}
    </div>
  );
}

