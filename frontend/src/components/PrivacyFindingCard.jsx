import React from "react";
import {
  Mail,
  Phone,
  CreditCard,
  FileText,
  User,
  MapPin,
  CheckCircle,
  XCircle,
  RotateCcw,
  ShieldAlert,
  Lock,
  Check
} from "lucide-react";

export default function PrivacyFindingCard({
  finding,
  isSelected,
  onToggleSelect,
  onUpdateStatus,
  updating
}) {
  const {
    id,
    entity_type,
    masked_value,
    risk_level,
    detection_method,
    confidence,
    page_number,
    explanation,
    review_status,
    is_redacted
  } = finding;

  // Icon selector based on entity type
  const getEntityIcon = (type) => {
    switch (type) {
      case "EMAIL":
        return <Mail size={15} />;
      case "PHONE":
        return <Phone size={15} />;
      case "CREDIT_CARD":
      case "BANK_ACCOUNT":
        return <CreditCard size={15} />;
      case "PAN_CARD":
      case "AADHAAR":
      case "PASSPORT":
        return <FileText size={15} />;
      case "PERSON_NAME":
        return <User size={15} />;
      case "ADDRESS":
        return <MapPin size={15} />;
      default:
        return <ShieldAlert size={15} />;
    }
  };

  const getRiskClass = (risk) => {
    switch (risk) {
      case "HIGH":
        return "badge-danger";
      case "MEDIUM":
        return "badge-warning";
      default:
        return "badge-info";
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "confirmed_sensitive":
        return <span className="status-pill confirmed"><Check size={11} /> Confirmed Sensitive</span>;
      case "not_sensitive":
        return <span className="status-pill dismissed"><XCircle size={11} /> Dismissed</span>;
      default:
        return <span className="status-pill pending">Needs Review</span>;
    }
  };

  return (
    <div className={`privacy-finding-card ${isSelected ? "selected" : ""} ${is_redacted ? "redacted" : ""}`}>
      {/* Checkbox for redaction selection */}
      <div className="finding-checkbox-col">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onToggleSelect(id)}
          disabled={is_redacted}
          title={is_redacted ? "Already redacted" : "Select for permanent redaction"}
          className="finding-checkbox"
        />
      </div>

      {/* Main Content */}
      <div className="finding-body">
        <div className="finding-top-row">
          <div className="finding-type-group">
            <span className="finding-type-icon">{getEntityIcon(entity_type)}</span>
            <span className="finding-type-name">{entity_type.replace("_", " ")}</span>
            <span className={`badge ${getRiskClass(risk_level)}`}>{risk_level} RISK</span>
            <span className="finding-page-pill">Page {page_number}</span>
          </div>

          <div className="finding-status-group">
            {is_redacted ? (
              <span className="status-pill redacted"><Lock size={11} /> Redacted</span>
            ) : (
              getStatusBadge(review_status)
            )}
          </div>
        </div>

        {/* Masked Sensitive Value */}
        <div className="finding-value-row">
          <span className="finding-value-label">Detected Pattern:</span>
          <code className="finding-masked-code">{masked_value}</code>
          <span className="finding-conf">({Math.round((confidence || 1.0) * 100)}% match)</span>
        </div>

        {/* Rationale Explanation */}
        {explanation && (
          <p className="finding-explanation">{explanation}</p>
        )}

        {/* Action Controls for User Review */}
        {!is_redacted && (
          <div className="finding-actions-row">
            <span className="action-hint">User Verification:</span>
            {review_status !== "confirmed_sensitive" && (
              <button
                className="btn-action confirm"
                onClick={() => onUpdateStatus(id, "confirmed_sensitive")}
                disabled={updating}
                title="Confirm this is sensitive personal/financial information"
              >
                <CheckCircle size={13} />
                <span>Confirm Sensitive</span>
              </button>
            )}

            {review_status !== "not_sensitive" && (
              <button
                className="btn-action dismiss"
                onClick={() => onUpdateStatus(id, "not_sensitive")}
                disabled={updating}
                title="Mark as false positive or non-sensitive"
              >
                <XCircle size={13} />
                <span>Dismiss (Not Sensitive)</span>
              </button>
            )}

            {review_status !== "needs_review" && (
              <button
                className="btn-action reset"
                onClick={() => onUpdateStatus(id, "needs_review")}
                disabled={updating}
                title="Reset to needs review"
              >
                <RotateCcw size={12} />
                <span>Reset</span>
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

