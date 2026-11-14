import React from "react";
import { ShieldAlert, ShieldCheck, AlertTriangle, Info, CheckCircle2, AlertOctagon } from "lucide-react";

export default function PrivacyReport({ report, onRescan, scanning }) {
  if (!report) return null;

  const { risk_summary, total_findings, recommended_actions, filename } = report;
  const overallRisk = risk_summary?.overall_risk || "LOW";

  const getRiskBadge = (risk) => {
    switch (risk) {
      case "CRITICAL":
      case "HIGH":
        return {
          icon: <AlertOctagon size={18} className="text-danger" />,
          label: "Critical Risk Detected",
          className: "risk-badge-danger",
          desc: "Sensitive statutory identifiers or financial accounts exposed."
        };
      case "MODERATE":
        return {
          icon: <AlertTriangle size={18} className="text-warning" />,
          label: "Moderate Privacy Risk",
          className: "risk-badge-warning",
          desc: "Personal contact endpoints or residential details identified."
        };
      case "LOW":
        return {
          icon: <Info size={18} className="text-primary" />,
          label: "Low Privacy Risk",
          className: "risk-badge-info",
          desc: "General personal names or public business context."
        };
      default:
        return {
          icon: <ShieldCheck size={18} className="text-success" />,
          label: "Clean & Safe",
          className: "risk-badge-success",
          desc: "No sensitive personal or financial identifiers found."
        };
    }
  };

  const badgeInfo = getRiskBadge(overallRisk);

  return (
    <div className="card privacy-report-card">
      <div className="privacy-report-header">
        <div className="privacy-title-group">
          <div className="privacy-shield-icon">
            <ShieldAlert size={26} className="text-accent" />
          </div>
          <div>
            <h3>AI Privacy & Sensitive Information Assessment</h3>
            <span className="privacy-subtitle">
              Automated compliance and data leakage scanning for <strong>{filename}</strong>
            </span>
          </div>
        </div>

        <div className="privacy-header-actions">
          <button
            className="btn btn-secondary rescan-btn"
            onClick={onRescan}
            disabled={scanning}
            title="Re-run privacy scan"
          >
            {scanning ? "Scanning..." : "Rescan Document"}
          </button>
        </div>
      </div>

      {/* Risk Level Banner */}
      <div className={`risk-banner ${badgeInfo.className}`}>
        <div className="risk-banner-left">
          {badgeInfo.icon}
          <div>
            <div className="risk-banner-label">{badgeInfo.label}</div>
            <div className="risk-banner-desc">{badgeInfo.desc}</div>
          </div>
        </div>
        <div className="risk-banner-rating">
          <span>Overall Rating:</span>
          <strong>{overallRisk}</strong>
        </div>
      </div>

      {/* Metric Tiles */}
      <div className="privacy-metrics-grid">
        <div className="privacy-metric-tile">
          <span className="metric-label">Total Findings</span>
          <span className="metric-value">{total_findings}</span>
        </div>
        <div className="privacy-metric-tile danger">
          <span className="metric-label">High Risk (Gov/Bank)</span>
          <span className="metric-value text-danger">{risk_summary?.high || 0}</span>
        </div>
        <div className="privacy-metric-tile warning">
          <span className="metric-label">Medium Risk (Contact)</span>
          <span className="metric-value text-warning">{risk_summary?.medium || 0}</span>
        </div>
        <div className="privacy-metric-tile info">
          <span className="metric-label">Low Risk (Names/Public)</span>
          <span className="metric-value text-info">{risk_summary?.low || 0}</span>
        </div>
      </div>

      {/* Recommended Actions */}
      {recommended_actions && recommended_actions.length > 0 && (
        <div className="privacy-recommendations">
          <div className="recommendations-title">
            <CheckCircle2 size={15} className="text-primary" />
            <span>Recommended Compliance Actions:</span>
          </div>
          <ul className="recommendations-list">
            {recommended_actions.map((rec, i) => (
              <li key={i}>{rec}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

