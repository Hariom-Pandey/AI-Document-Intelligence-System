import React, { useEffect, useState } from "react";
import {
  FileText,
  LayoutDashboard,
  FolderOpen,
  UploadCloud,
  MessageSquare,
  Search,
  Activity,
  Scale
} from "lucide-react";
import { api } from "../services/api";

export default function Navbar({ activePage, setActivePage }) {
  const [backendOnline, setBackendOnline] = useState(null);

  useEffect(() => {
    const check = async () => {
      try {
        await api.getHealth();
        setBackendOnline(true);
      } catch {
        setBackendOnline(false);
      }
    };
    check();
    const interval = setInterval(check, 10000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: <LayoutDashboard size={18} /> },
    { id: "library", label: "Library & Upload", icon: <FolderOpen size={18} /> },
    { id: "consistency", label: "Consistency & Conflicts", icon: <Scale size={18} /> },
    { id: "chat", label: "Document Chat", icon: <MessageSquare size={18} /> },
    { id: "search", label: "Semantic Search", icon: <Search size={18} /> },
  ];

  return (
    <header className="navbar">
      <div className="nav-brand" onClick={() => setActivePage("dashboard")}>
        <div className="brand-icon">
          <FileText size={22} />
        </div>
        <div>
          <h1 className="brand-title">DocuIntellect</h1>
          <span className="brand-subtitle">AI Document Intelligence System</span>
        </div>
      </div>

      <nav className="nav-links">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`nav-link ${activePage === item.id ? "active" : ""}`}
            onClick={() => setActivePage(item.id)}
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="nav-status">
        <div className={`status-pill ${backendOnline ? "online" : backendOnline === false ? "offline" : "checking"}`}>
          <span className="status-dot" />
          <span>{backendOnline ? "Backend Connected" : backendOnline === false ? "Backend Offline" : "Connecting..."}</span>
        </div>
      </div>
    </header>
  );
}

