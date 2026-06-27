import { useEffect, useState, useRef } from "react";
import axios from "axios";
import "./App.css";

const API = "http://127.0.0.1:8000";
const HISTORY_KEY = "legal-rag-history";

function parseAnswer(raw) {
  if (!raw) return { text: "", sources: [] };
  const parts = raw.split("SOURCES USED");
  const text = parts[0].trim();
  const sources = [];
  if (parts[1]) {
    const lines = parts[1].split("\n");
    let current = {};
    for (const line of lines) {
      const l = line.trim();
      if (l.startsWith("PDF Name")) current.pdf = l.split(":").slice(1).join(":").trim();
      if (l.startsWith("Page No")) {
        current.page = l.split(":").slice(1).join(":").trim();
        if (current.pdf) { sources.push({ ...current }); current = {}; }
      }
    }
  }
  return { text, sources };
}

function App() {
  const [question, setQuestion]           = useState("");
  const [answer, setAnswer]               = useState("");
  const [keyword, setKeyword]             = useState("");
  const [matches, setMatches]             = useState([]);
  const [globalKeyword, setGlobalKeyword] = useState("");
  const [globalResults, setGlobalResults] = useState([]);
  const [agreement, setAgreement]         = useState("");
  const [agreements, setAgreements]       = useState([]);
  const [loading, setLoading]             = useState(false);
  const [confidence, setConfidence]       = useState(0);
  const [parsedSources, setParsedSources] = useState([]);
  const [copied, setCopied]               = useState(false);

  const [awaitingSelection, setAwaitingSelection] = useState(false);
  const [agreementOptions, setAgreementOptions]   = useState([]);
  const [pendingQuestion, setPendingQuestion]     = useState("");
  const [pinnedAgreement, setPinnedAgreement]     = useState(null);

  const [viewerPdf, setViewerPdf]   = useState(null);
  const [viewerPage, setViewerPage] = useState(1);
  const [citedPages, setCitedPages] = useState([]);
  const [citedIndex, setCitedIndex] = useState(0);
  const iframeRef                   = useRef(null);

  const [history, setHistory] = useState(() => {
    try { return JSON.parse(localStorage.getItem(HISTORY_KEY)) || []; }
    catch { return []; }
  });
  const [activeTab, setActiveTab]         = useState("ask");
  const [historySearch, setHistorySearch] = useState("");
  const [darkMode, setDarkMode]           = useState(true);

  const saveToHistory = (q, a, pdf) => {
    const entry = { id: Date.now(), question: q, answer: a, pdf: pdf || null, timestamp: new Date().toLocaleString() };
    const updated = [entry, ...history].slice(0, 100);
    setHistory(updated);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
  };

  const restoreFromHistory = (entry) => {
    setQuestion(entry.question);
    setAnswer(entry.answer);
    const { sources } = parseAnswer(entry.answer);
    setParsedSources(sources);
    setActiveTab("ask");
    if (entry.pdf) {
      setViewerPdf(entry.pdf);
      setViewerPage(1);
      setTimeout(() => {
        if (iframeRef.current) {
          iframeRef.current.src = "";
          setTimeout(() => { iframeRef.current.src = getPdfUrl(entry.pdf, 1); }, 50);
        }
      }, 100);
    }
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem(HISTORY_KEY);
  };

  const getPdfUrl = (pdfName, page) =>
    `${API}/pdf/${encodeURIComponent(pdfName)}#page=${page}`;

  const jumpToPage = (page) => {
    setViewerPage(page);
    if (iframeRef.current && viewerPdf) {
      iframeRef.current.src = "";
      setTimeout(() => { iframeRef.current.src = getPdfUrl(viewerPdf, page); }, 50);
    }
  };

  const copyAnswer = () => {
    navigator.clipboard.writeText(answerText).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const askQuestion = async (overrideAgreement = null) => {
    const q = overrideAgreement ? pendingQuestion : question;
    if (!q.trim()) return;
    try {
      setLoading(true);
      setAwaitingSelection(false);
      setAgreementOptions([]);
      setAnswer("");
      setConfidence(0);
      setParsedSources([]);
      setCopied(false);

      const payload = { question: q };
      if (overrideAgreement)    payload.agreement = overrideAgreement;
      else if (pinnedAgreement) payload.agreement = pinnedAgreement;

      const response = await axios.post(`${API}/ask`, payload);
      const data = response.data;

      if (data.requires_selection) {
        setPendingQuestion(q);
        setAgreementOptions(data.agreements);
        setAwaitingSelection(true);
        return;
      }

      setAnswer(data.answer);
      setConfidence(data.confidence || 0);
      const { sources } = parseAnswer(data.answer);
      setParsedSources(sources);
      saveToHistory(q, data.answer, data.source_pdf);

      if (data.source_pdf) {
        setViewerPdf(data.source_pdf);
        setCitedPages(data.cited_pages || []);
        setCitedIndex(0);
        const page = data.source_page || 1;
        setViewerPage(page);
        setTimeout(() => {
          if (iframeRef.current) {
            iframeRef.current.src = "";
            setTimeout(() => { iframeRef.current.src = getPdfUrl(data.source_pdf, page); }, 50);
          }
        }, 100);
      }
    } catch (err) {
      console.error(err);
      setAnswer("Failed to connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  const selectAgreement = (pdfName) => {
    setAwaitingSelection(false);
    setAgreementOptions([]);
    setPinnedAgreement(pdfName);
    setViewerPdf(pdfName);
    setViewerPage(1);
    setCitedPages([]);
    setCitedIndex(0);
    setTimeout(() => {
      if (iframeRef.current) {
        iframeRef.current.src = "";
        setTimeout(() => { iframeRef.current.src = getPdfUrl(pdfName, 1); }, 50);
      }
    }, 100);
  };

  const searchKeyword = async () => {
    if (!agreement) return;
    try {
      const response = await axios.get(`${API}/keyword-search`, { params: { keyword, agreement } });
      setMatches(response.data.matches);
    } catch (err) { console.error(err); }
  };

  const searchGlobal = async () => {
    if (!globalKeyword.trim()) return;
    try {
      const response = await axios.get(`${API}/keyword-search-all`, { params: { keyword: globalKeyword } });
      setGlobalResults(response.data.results || []);
    } catch (err) { console.error(err); }
  };

  useEffect(() => {
    axios.get(`${API}/agreements`)
      .then((r) => {
        const pdfs = r.data?.agreements || [];
        setAgreements(pdfs);
        if (pdfs.length > 0) setAgreement(pdfs[0]);
      })
      .catch((e) => console.error("Agreement load failed:", e));
  }, []);

  const shortName = (name) => name.replace(".pdf","").replace(".PDF","");
  const { text: answerText } = parseAnswer(answer);

  const filteredHistory = historySearch.trim()
    ? history.filter(e =>
        e.question.toLowerCase().includes(historySearch.toLowerCase()) ||
        (e.pdf && e.pdf.toLowerCase().includes(historySearch.toLowerCase()))
      )
    : history;

  return (
    <div className={`app ${darkMode ? "dark" : "light"}`}>

      <aside className="sidebar">
        <div className="logo-card">
          <div className="logo-icon">⚖️</div>
          <div>
            <h2>Legal RAG</h2>
            <p>Assistant</p>
          </div>
        </div>

        <div className="menu">
          <div className={`menu-item ${activeTab === "ask" ? "active" : ""}`} onClick={() => setActiveTab("ask")}>
            Ask Question
          </div>
          <div className={`menu-item ${activeTab === "history" ? "active" : ""}`} onClick={() => setActiveTab("history")}>
            History
            {history.length > 0 && <span className="history-badge">{history.length}</span>}
          </div>
        </div>

        <button className="theme-toggle" onClick={() => setDarkMode(!darkMode)}>
          {darkMode ? "☀️ Light" : "🌙 Dark"}
        </button>

        <div className="about-card">
          <h3>About</h3>
          <p>Query telecom MSAs and get grounded answers with citations.</p>
        </div>
      </aside>

      <div className="split-layout">
        <div className="qa-panel">

          {activeTab === "history" && (
            <div>
              <div className="header">
                <h1>History</h1>
                <p>Your recent questions</p>
              </div>
              <input
                type="text"
                value={historySearch}
                onChange={(e) => setHistorySearch(e.target.value)}
                placeholder="Search history..."
                style={{ marginBottom: "14px" }}
              />
              {filteredHistory.length === 0 ? (
                <div className="card">
                  <div className="empty-state">
                    <div className="empty-state-icon">📋</div>
                    <p>{historySearch ? "No matching history" : "No history yet"}</p>
                  </div>
                </div>
              ) : (
                <>
                  <button
                    onClick={clearHistory}
                    style={{ background: "rgba(239,68,68,0.2)", border: "1px solid rgba(239,68,68,0.35)", marginBottom: "14px" }}
                  >
                    Clear All
                  </button>
                  {filteredHistory.map((entry) => (
                    <div key={entry.id} className="history-item" onClick={() => restoreFromHistory(entry)}>
                      <div className="history-question">{entry.question}</div>
                      <div className="history-meta">
                        {entry.pdf && <span className="history-pdf">📄 {shortName(entry.pdf)}</span>}
                        <span className="history-time">{entry.timestamp}</span>
                      </div>
                      <div className="history-preview">{entry.answer.slice(0, 120)}...</div>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}

          {activeTab === "ask" && (
            <>
              <div className="header">
                <h1>Legal RAG Assistant</h1>
                <p>Ask questions about your telecom agreements</p>
              </div>

              <div className="card">
                <h2>Ask a Question</h2>
                <textarea
                  value={question}
                  onChange={(e) => {
                    setQuestion(e.target.value);
                    setAwaitingSelection(false);
                    setAgreementOptions([]);
                    setAnswer("");
                    setConfidence(0);
                    setParsedSources([]);
                  }}
                  placeholder="e.g. State the clause for confidentiality in the Topaz agreement"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) askQuestion();
                  }}
                />
                <button onClick={() => askQuestion()} disabled={loading}>
                  {loading ? "Thinking…" : "Ask"}
                </button>
              </div>

              {pinnedAgreement && (
                <div className="pinned-agreement-bar">
                  <span>📌 Searching in: <strong>{shortName(pinnedAgreement)}</strong></span>
                  <button className="clear-pin-btn" onClick={() => { setPinnedAgreement(null); setViewerPdf(null); setCitedPages([]); }}>
                    Clear ✕
                  </button>
                </div>
              )}

              {awaitingSelection && (
                <div className="card">
                  <h2>Multiple agreements found — please select one</h2>
                  <p style={{ color: "var(--text-muted)", marginBottom: "16px", fontSize: "13px" }}>
                    Your question matches more than one agreement. Click the one you want to search.
                  </p>
                  <div className="agreement-selection-grid">
                    {agreementOptions.map((opt) => (
                      <div key={opt.pdf_name} className="agreement-option-card" onClick={() => selectAgreement(opt.pdf_name)}>
                        <h3>{opt.display_name}</h3>
                        {opt.agreement_date && <p className="agreement-date">{opt.agreement_date}</p>}
                        <p className="agreement-filename">{opt.pdf_name}</p>
                        {opt.parties.length > 0 && (
                          <div className="agreement-parties">
                            <span>Parties</span>
                            <ul>{opt.parties.map((p, i) => <li key={i}>{p}</li>)}</ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="card">
                <h2>Answer</h2>
                <div className="answer-box">
                  {answerText ? (
                    <>
                      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "10px" }}>
                        <button
                          onClick={copyAnswer}
                          style={{
                            margin: 0,
                            padding: "5px 12px",
                            fontSize: "11px",
                            background: copied ? "rgba(34,197,94,0.2)" : "rgba(255,255,255,0.08)",
                            border: copied ? "1px solid rgba(34,197,94,0.4)" : "1px solid var(--border-2)",
                            color: copied ? "var(--green)" : "var(--text-dim)",
                            borderRadius: "6px",
                          }}
                        >
                          {copied ? "✓ Copied" : "Copy"}
                        </button>
                      </div>

                      <pre>{answerText}</pre>

                      {confidence > 0 && (
                        <div className="confidence-card" style={{
                          borderColor: confidence >= 80 ? "rgba(34,197,94,0.3)" : confidence >= 50 ? "rgba(245,158,11,0.3)" : "rgba(239,68,68,0.3)",
                          background: confidence >= 80 ? "rgba(34,197,94,0.07)" : confidence >= 50 ? "rgba(245,158,11,0.07)" : "rgba(239,68,68,0.07)"
                        }}>
                          <div className="confidence-label">Confidence</div>
                          <div className="confidence-row">
                            <div className="confidence-track">
                              <div className="confidence-fill" style={{
                                width: `${confidence}%`,
                                background: confidence >= 80 ? "var(--green)" : confidence >= 50 ? "var(--amber)" : "var(--red)"
                              }} />
                            </div>
                            <span className="confidence-pct" style={{
                              color: confidence >= 80 ? "var(--green)" : confidence >= 50 ? "var(--amber)" : "var(--red)"
                            }}>{confidence}%</span>
                          </div>
                        </div>
                      )}

                      {parsedSources.length > 0 && (
                        <div className="sources-section">
                          <div className="sources-label">Sources</div>
                          {parsedSources.map((s, i) => (
                            <div
                              key={i}
                              className="source-card"
                              onClick={() => {
                                const page = parseInt(s.page);
                                if (!isNaN(page)) { setViewerPdf(s.pdf); jumpToPage(page); }
                              }}
                            >
                              <div className="source-card-pdf">📄 {shortName(s.pdf)}</div>
                              <div className="source-card-meta">
                                <span className="source-card-path">{s.pdf}</span>
                                <span className="source-card-page">Page {s.page}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="empty-state">
                      <div className="empty-state-icon">⚖️</div>
                      <p>Your answer will appear here</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="card">
                <h2>Keyword Search</h2>
                <div className="keyword-row">
                  <select value={agreement} onChange={(e) => setAgreement(e.target.value)}>
                    {agreements.length === 0
                      ? <option value="">Loading…</option>
                      : agreements.map((item) => <option key={item} value={item}>{shortName(item)}</option>)
                    }
                  </select>
                  <input
                    type="text"
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && searchKeyword()}
                    placeholder="termination"
                  />
                  <button onClick={searchKeyword}>Search</button>
                </div>
              </div>

              {matches.length > 0 && (
                <div className="card">
                  <h2>Results ({matches.length})</h2>
                  {matches.map((match, i) => (
                    <div key={i} className="keyword-result">
                      <h4>Page {match.page_number}</h4>
                      {match.heading && <p>{match.heading}</p>}
                      <div dangerouslySetInnerHTML={{
                        __html: match.snippet.replaceAll("<<<HIGHLIGHT>>>","<mark>").replaceAll("<<<END>>>","</mark>")
                      }} />
                    </div>
                  ))}
                </div>
              )}

              <div className="card">
                <h2>Global Search</h2>
                <div className="keyword-row">
                  <input
                    type="text"
                    value={globalKeyword}
                    onChange={(e) => setGlobalKeyword(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && searchGlobal()}
                    placeholder="e.g. indemnification"
                    style={{ flex: 3 }}
                  />
                  <button onClick={searchGlobal} style={{ marginTop: 0 }}>Search All</button>
                </div>
              </div>

              {globalResults.length > 0 && (
                <div className="card">
                  <h2>
                    {globalResults.reduce((a, g) => a + g.count, 0)} matches across {globalResults.length} agreements
                  </h2>
                  {globalResults.map((group) => (
                    <div key={group.pdf_name} className="global-result-group">
                      <div className="global-result-header">
                        📄 {shortName(group.pdf_name)}
                        <span className="global-result-count">{group.count}</span>
                      </div>
                      {group.matches.map((match, i) => (
                        <div key={i} className="keyword-result">
                          <h4>Page {match.page_number}</h4>
                          {match.heading && <p>{match.heading}</p>}
                          <div dangerouslySetInnerHTML={{
                            __html: match.snippet.replaceAll("<<<HIGHLIGHT>>>","<mark>").replaceAll("<<<END>>>","</mark>")
                          }} />
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        <div className="pdf-panel">
          {viewerPdf ? (
            <>
              <div className="pdf-toolbar">
                <span className="pdf-name">📄 {shortName(viewerPdf)}</span>
                <span className="pdf-page-indicator">Page {viewerPage}</span>
                {citedPages.length > 0 && (
                  <div className="cited-nav">
                    <span>Cited:</span>
                    {citedPages.map((p, i) => (
                      <button
                        key={i}
                        className={`cited-page-btn ${i === citedIndex ? "active-cited" : ""}`}
                        onClick={() => { setCitedIndex(i); jumpToPage(p); }}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <iframe ref={iframeRef} src={getPdfUrl(viewerPdf, viewerPage)} className="pdf-iframe" title="PDF Viewer" />
            </>
          ) : (
            <div className="pdf-empty">
              <div className="pdf-empty-icon">📄</div>
              <p>Select an agreement to view the PDF here</p>
              <p className="pdf-empty-sub">The document will open automatically when you pick an agreement. Pages cited in answers will be highlighted.</p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

export default App;