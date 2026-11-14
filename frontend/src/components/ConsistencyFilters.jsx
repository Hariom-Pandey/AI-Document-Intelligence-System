import React from "react";
import { Search, Filter, SlidersHorizontal } from "lucide-react";

export default function ConsistencyFilters({
  activeCategory,
  onCategoryChange,
  activeStatus,
  onStatusChange,
  searchQuery,
  onSearchChange,
  categories = []
}) {
  const statusOptions = [
    { id: "ALL", label: "All Statuses" },
    { id: "needs_review", label: "Needs Review" },
    { id: "confirmed_conflict", label: "Confirmed" },
    { id: "valid_revision", label: "Valid Revision" },
    { id: "false_positive", label: "False Positive" },
    { id: "resolved", label: "Resolved" }
  ];

  return (
    <div className="consistency-filter-card">
      <div className="filter-top-row">
        {/* Search Bar */}
        <div className="filter-search-box">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            className="filter-input"
            placeholder="Search conflicting statements or documents..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
          />
        </div>

        {/* Status Dropdown */}
        <div className="filter-status-box">
          <Filter size={15} className="filter-icon" />
          <select
            className="filter-select"
            value={activeStatus}
            onChange={(e) => onStatusChange(e.target.value)}
          >
            {statusOptions.map((opt) => (
              <option key={opt.id} value={opt.id}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Category Pills Row */}
      <div className="category-pills-scroll">
        <button
          type="button"
          className={`cat-pill ${activeCategory === "ALL" ? "active" : ""}`}
          onClick={() => onCategoryChange("ALL")}
        >
          All Categories
        </button>

        {categories.map((cat) => (
          <button
            key={cat}
            type="button"
            className={`cat-pill ${activeCategory === cat ? "active" : ""}`}
            onClick={() => onCategoryChange(cat)}
          >
            {cat.replace(/_/g, " ")}
          </button>
        ))}
      </div>
    </div>
  );
}

