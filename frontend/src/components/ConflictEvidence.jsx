import React from "react";
import { Info, Cpu, Check, GitCommit, Layers } from "lucide-react";

export default function ConflictEvidence({ explanation, evidenceContext = {}, confidence, nliLabel }) {
  const isFallback = evidenceContext?.fallback_active;
  const detectionMethod = evidenceContext?.detection_method || (isFallback ? "semantic_rule_fallback" : "cross_encoder_nli");

  return (
    <div className="conflict-evidence-panel">
      {/* Explanation Banner */}
      <div className="evidence-explanation-row">
        <Info size={16} className="evidence-info-icon" />
        <p className="evidence-explanation-text">{explanation}</p>
      </div>

      {/* Structured Details Matrix */}
      <div className="evidence-details-grid">
        {evidenceContext?.subject && (
          <div className="evidence-detail-item">
            <span className="detail-label">Subject Metric:</span>
            <span className="detail-value highlight-value">{evidenceContext.subject}</span>
          </div>
        )}

        {evidenceContext?.value_a && (
          <div className="evidence-detail-item">
            <span className="detail-label">Doc A Value:</span>
            <span className="detail-value val-a">{evidenceContext.value_a}</span>
          </div>
        )}

        {evidenceContext?.value_b && (
          <div className="evidence-detail-item">
            <span className="detail-label">Doc B Value:</span>
            <span className="detail-value val-b">{evidenceContext.value_b}</span>
          </div>
        )}

        {evidenceContext?.date_a && (
          <div className="evidence-detail-item">
            <span className="detail-label">Doc A Date:</span>
            <span className="detail-value">{evidenceContext.date_a}</span>
          </div>
        )}

        {evidenceContext?.date_b && (
          <div className="evidence-detail-item">
            <span className="detail-label">Doc B Date:</span>
            <span className="detail-value">{evidenceContext.date_b}</span>
          </div>
        )}

        {evidenceContext?.role && (
          <div className="evidence-detail-item">
            <span className="detail-label">Role Context:</span>
            <span className="detail-value">{evidenceContext.role}</span>
          </div>
        )}

        {/* Model Inference Metadata */}
        <div className="evidence-detail-item meta-item">
          <span className="detail-label">Inference Engine:</span>
          <span className={`detail-value engine-badge ${isFallback ? "badge-fallback" : "badge-neural"}`}>
            <Cpu size={12} />
            <span>
              {isFallback ? "Rule/Cosine Fallback" : "Neural DeBERTa NLI"}
            </span>
          </span>
        </div>

        <div className="evidence-detail-item meta-item">
          <span className="detail-label">Confidence Score:</span>
          <div className="confidence-meter-container">
            <div
              className="confidence-meter-fill"
              style={{ width: `${Math.round((confidence || 0) * 100)}%` }}
            />
            <span className="confidence-percent">{Math.round((confidence || 0) * 100)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
}

