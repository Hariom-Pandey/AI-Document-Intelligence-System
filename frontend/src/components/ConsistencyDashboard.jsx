import React from "react";
import { AlertTriangle, CheckCircle, Scale, ShieldAlert, Layers, Hash } from "lucide-react";

export default function ConsistencyDashboard({
  totalPairs = 0,
  totalConflicts = 0,
  highConfidenceCount = 0,
  uncertainCount = 0,
  categoriesDistribution = {},
  documentCount = 0
}) {
  // Determine overall consistency severity status
  let healthLevel = "EXCELLENT";
  let healthMessage = "High consistency detected across compared documents.";
  let healthBadgeClass = "health-green";
  let HealthIcon = CheckCircle;

  if (highConfidenceCount > 3 || (totalConflicts > 5 && highConfidenceCount > 0)) {
    healthLevel = "CRITICAL";
    healthMessage = "Multiple critical contradictions and conflicting contractual/financial figures identified.";
    healthBadgeClass = "health-red";
    HealthIcon = ShieldAlert;
  } else if (totalConflicts > 0) {
    healthLevel = "MODERATE";
    healthMessage = "Potential statement or numerical discrepancies detected that require human verification.";
    healthBadgeClass = "health-amber";
    HealthIcon = AlertTriangle;
  }

  return (
    <div className="consistency-dashboard-card">
      {/* Executive Status Banner */}
      <div className={`health-banner ${healthBadgeClass}`}>
        <div className="health-icon-box">
          <HealthIcon size={24} />
        </div>
        <div className="health-text">
          <div className="health-title-row">
            <span className="health-label">System Consistency Audit:</span>
            <span className="health-rating">{healthLevel}</span>
          </div>
          <p className="health-desc">{healthMessage}</p>
        </div>
      </div>

      {/* Metric Tiles Grid */}
      <div className="consistency-metrics-grid">
        <div className="metric-tile">
          <div className="metric-icon-box blue-box">
            <Layers size={18} />
          </div>
          <div className="metric-info">
            <span className="metric-value">{totalPairs}</span>
            <span className="metric-label">Statement Pairs Analyzed</span>
          </div>
        </div>

        <div className="metric-tile">
          <div className="metric-icon-box red-box">
            <AlertTriangle size={18} />
          </div>
          <div className="metric-info">
            <span className="metric-value">{totalConflicts}</span>
            <span className="metric-label">Total Conflicts Detected</span>
          </div>
        </div>

        <div className="metric-tile">
          <div className="metric-icon-box amber-box">
            <Scale size={18} />
          </div>
          <div className="metric-info">
            <span className="metric-value">{highConfidenceCount}</span>
            <span className="metric-label">High Confidence Conflicts</span>
          </div>
        </div>

        <div className="metric-tile">
          <div className="metric-icon-box slate-box">
            <Hash size={18} />
          </div>
          <div className="metric-info">
            <span className="metric-value">{uncertainCount}</span>
            <span className="metric-label">Uncertain / Needs Review</span>
          </div>
        </div>
      </div>

      {/* Category Breakdown Chips */}
      {Object.keys(categoriesDistribution).length > 0 && (
        <div className="category-breakdown-row">
          <span className="breakdown-title">Conflict Distribution:</span>
          <div className="breakdown-chips">
            {Object.entries(categoriesDistribution).map(([cat, count]) => (
              <span key={cat} className="breakdown-chip">
                <span className="chip-label">{cat.replace(/_/g, " ")}:</span>
                <strong className="chip-count">{count}</strong>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

