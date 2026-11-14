import React, { useState, useEffect, useRef } from "react";
import {
  MessageSquare,
  Send,
  Sparkles,
  AlertCircle,
  Loader2,
  Bot,
  User,
  HelpCircle,
  Copy,
  Check,
  Trash2,
  RotateCcw
} from "lucide-react";
import SourceCitation from "./SourceCitation";
import { api } from "../services/api";

// Safe inline Markdown Parser for structured rendering
function formatInline(text) {
  if (!text) return null;

  // Split by bold (**bold**) and inline code (`code`)
  const parts = text.split(/(\*\*.*?\*\*|`.*?`|\*.*?\*)/g);

  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**") && part.length >= 4) {
      return <strong key={i} className="md-bold">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`") && part.length >= 2) {
      return <code key={i} className="md-code">{part.slice(1, -1)}</code>;
    }
    if (part.startsWith("*") && part.endsWith("*") && part.length >= 2) {
      return <em key={i} className="md-italic">{part.slice(1, -1)}</em>;
    }
    return part;
  });
}

function FormattedMessage({ text }) {
  if (!text) return null;

  // Normalize linebreaks
  const rawBlocks = text.split(/\n\s*\n/);

  return (
    <div className="formatted-chat-message">
      {rawBlocks.map((block, bIdx) => {
        const trimmed = block.trim();
        if (!trimmed) return null;

        // Blockquote
        if (trimmed.startsWith(">")) {
          const quoteLines = trimmed.split("\n").map(l => l.replace(/^>\s*/, ""));
          return (
            <blockquote key={bIdx} className="chat-blockquote">
              {quoteLines.map((ql, qIdx) => (
                <p key={qIdx}>{formatInline(ql)}</p>
              ))}
            </blockquote>
          );
        }

        // Numbered list
        const lines = trimmed.split("\n");
        const isNumbered = lines.length > 0 && lines.every(l => /^\s*\d+[\.\)]\s+/.test(l));
        if (isNumbered) {
          return (
            <ol key={bIdx} className="chat-ol">
              {lines.map((l, lIdx) => {
                const cleanLine = l.replace(/^\s*\d+[\.\)]\s+/, "");
                return <li key={lIdx}>{formatInline(cleanLine)}</li>;
              })}
            </ol>
          );
        }

        // Bulleted list (• or - or *)
        const isBulletList = lines.length > 0 && lines.every(l => /^\s*(?:[•\*\-]|--)\s+/.test(l));
        if (isBulletList) {
          return (
            <ul key={bIdx} className="chat-ul">
              {lines.map((l, lIdx) => {
                const cleanLine = l.replace(/^\s*(?:[•\*\-]|--)\s+/, "");
                return <li key={lIdx}>{formatInline(cleanLine)}</li>;
              })}
            </ul>
          );
        }

        // Mixed paragraphs with inline bullet points
        const containsBullets = lines.some(l => /^\s*(?:[•\*\-]|--)\s+/.test(l));
        if (containsBullets && lines.length > 1) {
          return (
            <div key={bIdx} className="chat-mixed-block">
              {lines.map((l, lIdx) => {
                if (/^\s*(?:[•\*\-]|--)\s+/.test(l)) {
                  const cleanLine = l.replace(/^\s*(?:[•\*\-]|--)\s+/, "");
                  return (
                    <div key={lIdx} className="chat-bullet-item">
                      <span className="chat-bullet-dot">•</span>
                      <span>{formatInline(cleanLine)}</span>
                    </div>
                  );
                }
                if (/^\s*\d+[\.\)]\s+/.test(l)) {
                  const numMatch = l.match(/^\s*(\d+)[\.\)]\s+(.*)/);
                  return (
                    <div key={lIdx} className="chat-num-item">
                      <span className="chat-num-badge">{numMatch[1]}.</span>
                      <span>{formatInline(numMatch[2])}</span>
                    </div>
                  );
                }
                return (
                  <p key={lIdx} className="chat-lead-line">
                    {formatInline(l)}
                  </p>
                );
              })}
            </div>
          );
        }

        // Standard paragraph
        return (
          <p key={bIdx} className="chat-p">
            {formatInline(trimmed)}
          </p>
        );
      })}
    </div>
  );
}

export default function ChatPanel({ documentId, documentTitle, category }) {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [isClearing, setIsClearing] = useState(false);
  const messagesEndRef = useRef(null);

  // Load chat history if documentId exists
  useEffect(() => {
    if (documentId) {
      api.getChatHistory(documentId)
        .then((history) => {
          if (history && history.length > 0) {
            const formatted = [];
            history.forEach((h) => {
              formatted.push({
                sender: "user",
                text: h.question,
                timestamp: h.created_at,
              });
              formatted.push({
                sender: "ai",
                text: h.answer,
                citations: h.citations || [],
                hasEvidence: (h.citations || []).length > 0,
                timestamp: h.created_at,
              });
            });
            setMessages(formatted);
          } else {
            setMessages([
              {
                sender: "ai",
                text: `**Hello!** I'm your grounded AI assistant for **"${documentTitle || "this document"}"**.\n\nAsk me any question regarding facts, projects, clauses, metrics, or mechanisms. Every answer is synthesized with verified page citations.`,
                citations: [],
                hasEvidence: false,
              },
            ]);
          }
        })
        .catch(() => {
          setMessages([
            {
              sender: "ai",
              text: `**Hello!** Ask me anything about **"${documentTitle || "this document"}"**. I'll retrieve relevant pages and provide cited answers.`,
              citations: [],
              hasEvidence: false,
            },
          ]);
        });
    }
  }, [documentId, documentTitle]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (queryText) => {
    const q = (queryText || question).trim();
    if (!q || loading) return;

    setError(null);
    const newMsg = { sender: "user", text: q, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, newMsg]);
    setQuestion("");
    setLoading(true);

    try {
      const res = await api.askDocument(documentId, q);
      const aiMsg = {
        sender: "ai",
        text: res.answer,
        citations: res.citations || [],
        hasEvidence: res.has_evidence,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      setError(err.message || "Failed to get an answer.");
      setMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: "An error occurred while retrieving or synthesizing an answer. Please verify backend status and document indexing.",
          citations: [],
          hasEvidence: false,
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text, idx) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleClearChat = async () => {
    if (isClearing || !documentId) return;
    setIsClearing(true);
    try {
      await api.clearChatHistory(documentId);
      setMessages([
        {
          sender: "ai",
          text: `Chat history cleared. I'm ready for new questions about **"${documentTitle || "this document"}"**.`,
          citations: [],
          hasEvidence: false,
        },
      ]);
    } catch (e) {
      console.error("Failed to clear chat history", e);
    } finally {
      setIsClearing(false);
    }
  };

  // Dynamic suggested prompts tailored to document category
  const getSuggestedPrompts = () => {
    const c = (category || "").toLowerCase();
    const t = (documentTitle || "").toLowerCase();

    if (c === "resume" || t.includes("cv") || t.includes("resume")) {
      return [
        "What projects has the candidate built?",
        "What are the core technical skills & programming languages?",
        "What is the candidate's educational background and CGPA?",
        "Summarize professional achievements and tools.",
      ];
    }
    if (c === "academic" || t.includes("ieee") || t.includes("paper") || t.includes("review")) {
      return [
        "What are the primary research questions?",
        "What methodology or framework is proposed?",
        "What are the key experimental results and findings?",
        "What is the conclusion and future research scope?",
      ];
    }
    if (c === "legal" || t.includes("contract") || t.includes("agreement") || t.includes("nda")) {
      return [
        "What are the liquidated damages or penalties for breach?",
        "What is the governing law and legal jurisdiction?",
        "What are the confidentiality obligations and term?",
        "What are the termination conditions?",
      ];
    }
    if (c === "financial" || t.includes("invoice") || t.includes("finance") || t.includes("statement")) {
      return [
        "What are the total amounts, fees, and payment deadlines?",
        "Who are the payees and accounts involved?",
        "What are the financial terms and conditions?",
        "Summarize the key transactions and dates.",
      ];
    }
    return [
      "What is the main purpose of this document?",
      "Summarize the key findings or sections.",
      "What dates, obligations, or metrics are mentioned?",
      "How does the core workflow or mechanism operate?",
    ];
  };

  const sampleQuestions = getSuggestedPrompts();

  return (
    <div className="chat-container">
      {/* Chat Header */}
      <div className="chat-header">
        <div className="chat-title">
          <Bot size={20} className="accent-icon" />
          <div>
            <h3>Grounded Document Q&A</h3>
            <span className="chat-subtitle">
              Contextual RAG synthesis with verified page citations
            </span>
          </div>
        </div>

        <div className="chat-header-actions">
          {messages.length > 1 && (
            <button
              className="chat-action-btn"
              onClick={handleClearChat}
              disabled={isClearing || loading}
              title="Clear chat history"
            >
              <RotateCcw size={14} />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>

      {/* Messages List */}
      <div className="chat-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message-row ${msg.sender}`}>
            <div className="message-avatar">
              {msg.sender === "user" ? <User size={16} /> : <Bot size={16} />}
            </div>

            <div className="message-bubble">
              {/* Message Header with Copy button for AI */}
              {msg.sender === "ai" && !msg.isError && (
                <div className="message-bubble-header">
                  <span className="ai-badge">DocuIntellect Grounded AI</span>
                  <button
                    className="copy-answer-btn"
                    onClick={() => handleCopy(msg.text, index)}
                    title="Copy Answer"
                  >
                    {copiedIndex === index ? (
                      <>
                        <Check size={12} className="text-success" />
                        <span>Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy size={12} />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                </div>
              )}

              {/* Formatted Content */}
              <div className="message-text">
                <FormattedMessage text={msg.text} />
              </div>

              {/* Citations tray for AI responses */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="citations-tray">
                  <div className="citations-tray-title">
                    <Sparkles size={13} />
                    <span>Evidence Citations ({msg.citations.length})</span>
                  </div>
                  <div className="citations-list">
                    {msg.citations.map((cite, cIdx) => (
                      <SourceCitation key={cIdx} citation={cite} index={cIdx} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message-row ai">
            <div className="message-avatar">
              <Bot size={16} />
            </div>
            <div className="message-bubble loading-bubble">
              <Loader2 size={16} className="animate-spin text-accent" />
              <span>Analyzing document context and synthesizing grounded answer...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions */}
      {messages.length <= 2 && (
        <div className="suggested-prompts">
          <span className="suggested-title">
            <HelpCircle size={14} /> Suggested Questions:
          </span>
          <div className="prompt-buttons">
            {sampleQuestions.map((prompt, pIdx) => (
              <button
                key={pIdx}
                className="prompt-pill"
                onClick={() => handleSend(prompt)}
                disabled={loading}
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input row */}
      {error && <div className="alert alert-error">{error}</div>}

      <form
        className="chat-input-bar"
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
      >
        <input
          type="text"
          placeholder={`Ask anything about ${documentTitle ? `"${documentTitle}"` : "this document"}...`}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          className="btn btn-primary send-btn"
          disabled={loading || !question.trim()}
        >
          <Send size={16} />
          <span>Ask</span>
        </button>
      </form>
    </div>
  );
}
