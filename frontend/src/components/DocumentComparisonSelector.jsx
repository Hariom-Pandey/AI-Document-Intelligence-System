import React, { useState, useMemo } from "react";
import {
  CheckSquare,
  Square,
  FileText,
  Search,
  RotateCw,
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  FileCode,
  FileSpreadsheet
} from "lucide-react";

export default function DocumentComparisonSelector({
  documents = [],
  selectedDocIds = [],
  onToggleDoc,
  onSelectAll,
  onClearAll,
  onReload,
  onNavigate,
  loading = false,
  disabled = false
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("ALL");

  // Get unique categories
  const categories = useMemo(() => {
    const cats = new Set();
    documents.forEach((d) => {
      if (d.category) cats.add(d.category);
    });
    return ["ALL", ...Array.from(cats)];
  }, [documents]);

  // Filtered documents for search & category
  const filteredDocs = useMemo(() => {
    return documents.filter((doc) => {
      const matchesSearch =
        !searchTerm.trim() ||
        doc.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (doc.category && doc.category.toLowerCase().includes(searchTerm.toLowerCase()));
      const matchesCategory =
        selectedCategory === "ALL" || doc.category === selectedCategory;
      return matchesSearch && matchesCategory;
    });
  }, [documents, searchTerm, selectedCategory]);

  const getFormatBadge = (filename = "") => {
    const ext = filename.split(".").pop().toUpperCase();
    if (ext === "PDF") return <span className="format-badge pdf-badge">PDF</span>;
    if (ext === "DOCX" || ext === "DOC") return <span className="format-badge docx-badge">DOCX</span>;
    if (ext === "TXT") return <span className="format-badge txt-badge">TXT</span>;
    return <span className="format-badge general-badge">{ext || "FILE"}</span>;
  };

  const handleSelectFirstTwo = () => {
    if (documents.length >= 2) {
      onClearAll();
      onToggleDoc(documents[0].id);
      onToggleDoc(documents[1].id);
    }
  };

  return (
    <div className="doc-selector-card">
      {/* Header */}
      <div className="selector-header">
        <div>
          <div className="selector-title-row">
            <h3 className="selector-title">Select Documents for Comparison</h3>
            <span className="doc-pool-pill">{documents.length} Available</span>
          </div>
          <p className="selector-subtitle">
            Choose 2 or more documents to detect contradictions, numerical mismatches, and date conflicts.
          </p>
        </div>

        <div className="selector-actions">
          {onReload && (
            <button
              type="button"
              className="selector-btn selector-btn-icon"
              onClick={onReload}
              disabled={disabled || loading}
              title="Refresh document list"
            >
              <RotateCw size={14} className={loading ? "spin-icon" : ""} />
            </button>
          )}

          {documents.length >= 2 && (
            <button
              type="button"
              className="selector-btn"
              onClick={handleSelectFirstTwo}
              disabled={disabled || loading}
              title="Select first two documents"
            >
              Select First 2
            </button>
          )}

          <button
            type="button"
            className="selector-btn"
            onClick={onSelectAll}
            disabled={disabled || loading || documents.length === 0}
          >
            Select All
          </button>

          <button
            type="button"
            className="selector-btn"
            onClick={onClearAll}
            disabled={disabled || loading || selectedDocIds.length === 0}
          >
            Clear
          </button>
        </div>
      </div>

      {/* Filter / Search Bar if multiple documents */}
      {documents.length > 3 && (
        <div className="selector-toolbar">
          <div className="selector-search-box">
            <Search size={14} className="search-icon" />
            <input
              type="text"
              placeholder="Search documents by name or category..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              disabled={disabled}
            />
            {searchTerm && (
              <button
                type="button"
                className="clear-search-btn"
                onClick={() => setSearchTerm("")}
              >
                ×
              </button>
            )}
          </div>

          {categories.length > 2 && (
            <div className="selector-category-pills">
              {categories.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  className={`cat-pill ${selectedCategory === cat ? "active" : ""}`}
                  onClick={() => setSelectedCategory(cat)}
                >
                  {cat}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Body States */}
      {loading ? (
        <div className="selector-loading-state">
          <RotateCw size={24} className="spin-icon text-cyan" />
          <span>Loading processed documents...</span>
        </div>
      ) : documents.length === 0 ? (
        <div className="selector-empty-state">
          <UploadCloud size={38} className="empty-upload-icon" />
          <h4>No Ready Documents Found</h4>
          <p>
            Cross-document contradiction detection requires at least 2 processed documents with extracted text.
          </p>
          {onNavigate && (
            <button
              type="button"
              className="btn-primary-action upload-nav-btn"
              onClick={() => onNavigate("library")}
            >
              <UploadCloud size={16} />
              <span>Go to Library & Upload</span>
            </button>
          )}
        </div>
      ) : filteredDocs.length === 0 ? (
        <div className="selector-no-results">
          <AlertCircle size={20} />
          <span>No documents match your search "{searchTerm}".</span>
          <button
            type="button"
            className="link-btn"
            onClick={() => {
              setSearchTerm("");
              setSelectedCategory("ALL");
            }}
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="doc-selector-grid">
          {filteredDocs.map((doc) => {
            const isSelected = selectedDocIds.includes(doc.id);
            return (
              <div
                key={doc.id}
                className={`doc-select-item ${isSelected ? "selected" : ""}`}
                onClick={() => !disabled && onToggleDoc(doc.id)}
              >
                <div className="item-checkbox">
                  {isSelected ? (
                    <CheckSquare size={18} className="checkbox-active" />
                  ) : (
                    <Square size={18} className="checkbox-inactive" />
                  )}
                </div>

                <div className="item-content">
                  <div className="item-title-row">
                    <FileText size={15} className="item-file-icon" />
                    <span className="item-filename" title={doc.filename}>
                      {doc.filename}
                    </span>
                  </div>

                  <div className="item-meta-row">
                    {getFormatBadge(doc.filename)}
                    <span className="doc-tag-badge">
                      {doc.category || "General"}
                    </span>
                    <span className="item-pages">
                      {doc.page_count || 1} {doc.page_count === 1 ? "page" : "pages"}
                    </span>
                    {isSelected && (
                      <span className="selected-tag">Selected</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Footer */}
      <div className="selector-footer">
        <span className="selected-count">
          <strong>{selectedDocIds.length}</strong> of {documents.length} documents selected
        </span>

        {selectedDocIds.length >= 2 ? (
          <span className="selection-ready">
            <CheckCircle2 size={14} />
            <span>Ready for cross-document consistency audit</span>
          </span>
        ) : (
          <span className="selection-warning">
            * Please select at least 2 documents to initiate consistency analysis.
          </span>
        )}
      </div>
    </div>
  );
}
