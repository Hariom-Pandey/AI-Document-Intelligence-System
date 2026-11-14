import React from "react";
import { Filter, Search, Tag, AlertTriangle } from "lucide-react";

export default function RiskDistribution({
  categoryDistribution,
  riskSummary,
  selectedRisk,
  onSelectRisk,
  selectedCategory,
  onSelectCategory,
  selectedStatus,
  onSelectStatus,
  searchQuery,
  onSearchChange,
  totalCount
}) {
  const categories = Object.keys(categoryDistribution || {});

  return (
    <div className="risk-distribution-container">
      {/* Risk Filter Bar */}
      <div className="risk-filter-row">
        <div className="risk-pills-group">
          <button
            className={`risk-pill ${selectedRisk === "ALL" ? "active" : ""}`}
            onClick={() => onSelectRisk("ALL")}
          >
            All Risks ({totalCount})
          </button>
          <button
            className={`risk-pill danger ${selectedRisk === "HIGH" ? "active" : ""}`}
            onClick={() => onSelectRisk("HIGH")}
          >
            High Risk ({riskSummary?.high || 0})
          </button>
          <button
            className={`risk-pill warning ${selectedRisk === "MEDIUM" ? "active" : ""}`}
            onClick={() => onSelectRisk("MEDIUM")}
          >
            Medium Risk ({riskSummary?.medium || 0})
          </button>
          <button
            className={`risk-pill info ${selectedRisk === "LOW" ? "active" : ""}`}
            onClick={() => onSelectRisk("LOW")}
          >
            Low Risk ({riskSummary?.low || 0})
          </button>
        </div>

        {/* Status Dropdown Filter & Search */}
        <div className="risk-filter-controls">
          <div className="search-input-wrapper">
            <Search size={14} className="search-icon" />
            <input
              type="text"
              placeholder="Filter findings..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="finding-search-input"
            />
          </div>

          <select
            value={selectedStatus}
            onChange={(e) => onSelectStatus(e.target.value)}
            className="status-filter-select"
          >
            <option value="ALL">All Review Statuses</option>
            <option value="needs_review">Needs Review</option>
            <option value="confirmed_sensitive">Confirmed Sensitive</option>
            <option value="not_sensitive">Dismissed (Not Sensitive)</option>
          </select>
        </div>
      </div>

      {/* Category Chips */}
      {categories.length > 0 && (
        <div className="category-chips-row">
          <span className="chips-title">
            <Tag size={13} /> Categories:
          </span>
          <button
            className={`category-chip ${selectedCategory === "ALL" ? "active" : ""}`}
            onClick={() => onSelectCategory("ALL")}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              className={`category-chip ${selectedCategory === cat ? "active" : ""}`}
              onClick={() => onSelectCategory(cat)}
            >
              <span>{cat.replace("_", " ")}</span>
              <span className="chip-count">{categoryDistribution[cat]}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

