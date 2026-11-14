import React, { useState, useMemo } from "react";
import { Tag, Search, Filter, User, Building2, MapPin, Calendar, DollarSign, HelpCircle } from "lucide-react";

export default function EntityPanel({ entities = [] }) {
  const [selectedLabel, setSelectedLabel] = useState("ALL");
  const [searchTerm, setSearchTerm] = useState("");

  const labelIcons = {
    PERSON: <User size={14} />,
    ORG: <Building2 size={14} />,
    GPE: <MapPin size={14} />,
    LOC: <MapPin size={14} />,
    DATE: <Calendar size={14} />,
    MONEY: <DollarSign size={14} />,
  };

  // Group labels and counts
  const labelCounts = useMemo(() => {
    const counts = { ALL: entities.length };
    entities.forEach((ent) => {
      counts[ent.label] = (counts[ent.label] || 0) + 1;
    });
    return counts;
  }, [entities]);

  const uniqueLabels = useMemo(() => {
    const labels = Array.from(new Set(entities.map((e) => e.label)));
    return ["ALL", ...labels];
  }, [entities]);

  const filteredEntities = useMemo(() => {
    return entities.filter((ent) => {
      const matchLabel = selectedLabel === "ALL" || ent.label === selectedLabel;
      const matchSearch =
        searchTerm === "" ||
        ent.text.toLowerCase().includes(searchTerm.toLowerCase());
      return matchLabel && matchSearch;
    });
  }, [entities, selectedLabel, searchTerm]);

  if (!entities || entities.length === 0) {
    return (
      <div className="card empty-card">
        <Tag size={32} className="muted-icon" />
        <p>No named entities extracted from this document yet.</p>
      </div>
    );
  }

  return (
    <div className="entity-container">
      <div className="card-header-row">
        <div className="section-title">
          <Tag size={20} className="accent-icon" />
          <h3>Extracted Entities ({entities.length})</h3>
        </div>

        {/* Search */}
        <div className="search-pill">
          <Search size={14} />
          <input
            type="text"
            placeholder="Filter entities..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Label Filter Chips */}
      <div className="filter-chips">
        {uniqueLabels.map((label) => (
          <button
            key={label}
            className={`chip ${selectedLabel === label ? "active" : ""}`}
            onClick={() => setSelectedLabel(label)}
          >
            {labelIcons[label] || <Tag size={12} />}
            <span>{label}</span>
            <span className="chip-count">{labelCounts[label] || 0}</span>
          </button>
        ))}
      </div>

      {/* Entity Grid */}
      <div className="entities-grid">
        {filteredEntities.map((ent, idx) => (
          <div key={idx} className={`entity-pill label-${ent.label.toLowerCase()}`}>
            <span className="entity-icon">{labelIcons[ent.label] || <Tag size={12} />}</span>
            <span className="entity-text">{ent.text}</span>
            <span className="entity-type-badge">{ent.label}</span>
            {ent.page_number && (
              <span className="entity-page-badge">p.{ent.page_number}</span>
            )}
          </div>
        ))}
      </div>

      {filteredEntities.length === 0 && (
        <p className="no-matches">No entities match your search filter.</p>
      )}
    </div>
  );
}

