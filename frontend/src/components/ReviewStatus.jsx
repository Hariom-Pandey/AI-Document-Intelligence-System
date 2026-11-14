import React, { useState } from "react";
import { CheckCircle2, AlertTriangle, RefreshCw, XCircle, Clock } from "lucide-react";

export default function ReviewStatus({ currentStatus, onStatusChange, disabled = false }) {
  const [loading, setLoading] = useState(false);

  const statusConfigs = {
    needs_review: {
      label: "Needs Review",
      color: "badge-amber",
      icon: <Clock size={13} />
    },
    confirmed_conflict: {
      label: "Confirmed Conflict",
      color: "badge-red",
      icon: <AlertTriangle size={13} />
    },
    valid_revision: {
      label: "Valid Revision",
      color: "badge-green",
      icon: <RefreshCw size={13} />
    },
    false_positive: {
      label: "False Positive",
      color: "badge-gray",
      icon: <XCircle size={13} />
    },
    resolved: {
      label: "Resolved",
      color: "badge-cyan",
      icon: <CheckCircle2 size={13} />
    }
  };

  const handleUpdate = async (newStatus) => {
    if (newStatus === currentStatus || disabled || loading) return;
    setLoading(true);
    try {
      await onStatusChange(newStatus);
    } finally {
      setLoading(false);
    }
  };

  const current = statusConfigs[currentStatus] || statusConfigs.needs_review;

  return (
    <div className="review-status-container">
      <div className={`status-pill ${current.color}`}>
        {current.icon}
        <span>{current.label}</span>
      </div>

      <div className="status-action-group">
        {currentStatus !== "confirmed_conflict" && (
          <button
            type="button"
            className="status-btn btn-confirm"
            title="Confirm genuine contradiction"
            disabled={disabled || loading}
            onClick={() => handleUpdate("confirmed_conflict")}
          >
            Confirm
          </button>
        )}

        {currentStatus !== "valid_revision" && (
          <button
            type="button"
            className="status-btn btn-revision"
            title="Mark as valid update or version revision"
            disabled={disabled || loading}
            onClick={() => handleUpdate("valid_revision")}
          >
            Revision
          </button>
        )}

        {currentStatus !== "false_positive" && (
          <button
            type="button"
            className="status-btn btn-dismiss"
            title="Dismiss as false positive or non-conflicting"
            disabled={disabled || loading}
            onClick={() => handleUpdate("false_positive")}
          >
            Dismiss
          </button>
        )}

        {currentStatus !== "resolved" && (
          <button
            type="button"
            className="status-btn btn-resolve"
            title="Mark as resolved"
            disabled={disabled || loading}
            onClick={() => handleUpdate("resolved")}
          >
            Resolve
          </button>
        )}
      </div>
    </div>
  );
}

