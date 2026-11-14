import React, { useState } from "react";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import DocumentLibrary from "./pages/DocumentLibrary";
import DocumentDetail from "./pages/DocumentDetail";
import DocumentChat from "./pages/DocumentChat";
import SearchPage from "./pages/SearchPage";
import ConsistencyAnalyzer from "./pages/ConsistencyAnalyzer";
import "./App.css";

export default function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const [selectedDocId, setSelectedDocId] = useState(null);

  const handleSelectDocument = (docId, targetPage = "detail") => {
    setSelectedDocId(docId);
    setActivePage(targetPage);
  };

  return (
    <div className="app-container">
      <Navbar activePage={activePage} setActivePage={setActivePage} />

      <main className="main-content">
        {activePage === "dashboard" && (
          <Dashboard
            onSelectDocument={handleSelectDocument}
            onNavigate={(page) => setActivePage(page)}
          />
        )}

        {activePage === "library" && (
          <DocumentLibrary onSelectDocument={handleSelectDocument} />
        )}

        {activePage === "detail" && (
          <DocumentDetail
            documentId={selectedDocId}
            onBack={() => setActivePage("library")}
            onNavigateChat={(docId) => {
              setSelectedDocId(docId);
              setActivePage("chat");
            }}
          />
        )}

        {activePage === "chat" && (
          <DocumentChat initialDocId={selectedDocId} />
        )}

        {activePage === "search" && (
          <SearchPage onSelectDocument={handleSelectDocument} />
        )}

        {activePage === "consistency" && (
          <ConsistencyAnalyzer
            onSelectDocument={handleSelectDocument}
            onNavigate={(page) => setActivePage(page)}
          />
        )}
      </main>

      <footer className="app-footer">
        <p>DocuIntellect — AI Document Intelligence System with RAG Pipeline</p>
        <span className="footer-meta">FastAPI • PyMuPDF • Transformers • spaCy • FAISS</span>
      </footer>
    </div>
  );
}
