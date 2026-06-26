import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import {
  ShieldCheck, Activity, Send, AlertTriangle,
  CheckCircle2, XCircle, TrendingUp, Clock, Ban,
  DollarSign, RefreshCw, Wallet, MessageSquare, History
} from 'lucide-react';

const API_BASE = 'http://localhost:8004/api';
const STORAGE_KEY = 'ztd_session_v2';

// ─── Helpers ─────────────────────────────────────────────────────────────────
function loadSession() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : { messages: [], tradeHistory: [], stats: { success: 0, pending: 0, rejected: 0 } };
  } catch {
    return { messages: [], tradeHistory: [], stats: { success: 0, pending: 0, rejected: 0 } };
  }
}

function saveSession(messages, tradeHistory, stats) {
  try {
    // cap stored messages to last 50 to avoid quota overflow
    const trimmed = messages.slice(-50);
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ messages: trimmed, tradeHistory, stats }));
  } catch { /* storage full – ignore */ }
}

function fmtTime(iso) {
  try { return new Date(iso).toLocaleString(); }
  catch { return iso; }
}

function fmtUSD(v) {
  return Number(v || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// ─── StatCard ─────────────────────────────────────────────────────────────────
function StatCard({ icon: Icon, label, value, color, sublabel }) {
  return (
    <div className="stat-card glass-panel">
      <div className="stat-icon" style={{ color }}><Icon size={20} /></div>
      <div className="stat-body">
        <div className="stat-value" style={{ color }}>{value}</div>
        <div className="stat-label">{label}</div>
        {sublabel && <div className="stat-sublabel">{sublabel}</div>}
      </div>
    </div>
  );
}

// ─── Compact EventLogCard ────────────────────────────────────────────────────
function EventLogCard({ log }) {
  const [expanded, setExpanded] = useState(false);
  const isRejected = log.decision_code && (log.decision_code.startsWith('REJECTED') || log.decision_code === 'SCHEMA_ABORT' || log.decision_code === 'DENIED_HITL');
  const isPending  = log.decision_code === 'PENDING_HITL';
  const isApproved = log.decision_code === 'APPROVED_HITL';
  const badgeClass = isRejected ? 'decision-REJECTED' : isPending ? 'decision-PENDING_HITL' : isApproved ? 'decision-APPROVED' : 'decision-EXECUTED';

  return (
    <div className="event-log-card">
      {/* ── compact single-line header ── */}
      <div className="elc-row" onClick={() => setExpanded(e => !e)} style={{ cursor: 'pointer' }}>
        <span className={`decision-badge ${badgeClass}`}>{log.decision_code}</span>
        <span className="elc-ticker">{log.action !== 'N/A' ? `${log.action} ${log.ticker}` : log.ticker !== 'N/A' ? log.ticker : '—'}</span>
        <span className="elc-value">${fmtUSD(log.estimated_value_usd)}</span>
        <span className="elc-toggle">{expanded ? '▲' : '▼'}</span>
      </div>

      {/* ── expandable policy detail ── */}
      {expanded && (
        <div className="elc-detail">
          <ul className="check-list">
            <li>
              {log.consensus_match ? <CheckCircle2 size={13} className="passed" /> : <XCircle size={13} className="failed" />}
              Consensus: {log.consensus_match ? 'Matched' : 'Conflict'}
            </li>
            {(log.policy_checks_passed || []).map(c => (
              <li key={c}><CheckCircle2 size={13} className="passed" /> {c} — OK</li>
            ))}
            {(log.policy_checks_failed || []).map(c => (
              <li key={c}><XCircle size={13} className="failed" /> {c} — FAILED</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// ─── Trade History Row ────────────────────────────────────────────────────────
function TradeHistoryRow({ entry }) {
  const [showPrompt, setShowPrompt] = useState(false);
  const isRejected = entry.decision_code && (entry.decision_code.startsWith('REJECTED') || entry.decision_code === 'SCHEMA_ABORT' || entry.decision_code === 'DENIED_HITL');
  const isPending  = entry.decision_code === 'PENDING_HITL';
  const isApproved = entry.decision_code === 'APPROVED_HITL';
  const badgeClass = isRejected ? 'decision-REJECTED' : isPending ? 'decision-PENDING_HITL' : isApproved ? 'decision-APPROVED' : 'decision-EXECUTED';

  return (
    <div className="th-row">
      <div className="th-main" onClick={() => setShowPrompt(s => !s)}>
        <div className="th-left">
          <span className={`decision-badge ${badgeClass}`}>{entry.decision_code}</span>
          <span className="th-ticker">
            {entry.action && entry.action !== 'N/A' ? `${entry.action} ` : ''}
            {entry.ticker && entry.ticker !== 'N/A' ? entry.ticker : '—'}
          </span>
          {entry.estimated_value_usd > 0 && (
            <span className="th-value">${fmtUSD(entry.estimated_value_usd)}</span>
          )}
        </div>
        <div className="th-right">
          <span className="th-time">{fmtTime(entry.submittedAt)}</span>
          <span className="elc-toggle">{showPrompt ? '▲' : '▼'}</span>
        </div>
      </div>
      {showPrompt && entry.prompt && (
        <div className="th-prompt">
          <span className="th-prompt-label">Directive</span>
          <p>{entry.prompt}</p>
        </div>
      )}
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────
function App() {
  const session = loadSession();

  const [health,       setHealth]       = useState({ composite_score: 1.0, status: 'healthy' });
  const [pending,      setPending]      = useState([]);
  const [messages,     setMessages]     = useState(session.messages || []);
  const [tradeHistory, setTradeHistory] = useState(session.tradeHistory || []);
  const [inputValue,   setInputValue]   = useState('');
  const [isLoading,    setIsLoading]    = useState(false);
  const [portfolio,    setPortfolio]    = useState({ holdings: [], trades: [] });
  const [stats,        setStats]        = useState(session.stats || { success: 0, pending: 0, rejected: 0 });
  const [portfolioValue, setPortfolioValue] = useState(0);
  const [lastRefresh,  setLastRefresh]  = useState(null);
  const [activeTab,    setActiveTab]    = useState('console'); // 'console' | 'history'

  const chatEndRef = useRef(null);

  const calcPortfolioValue = useCallback((holdings) =>
    holdings.reduce((sum, h) => sum + h.quantity * h.average_price, 0), []);

  const buildStats = useCallback((auditEntries) => {
    let success = 0, pendingCount = 0, rejected = 0;
    auditEntries.forEach(e => {
      const code = e.decision_code || '';
      if (code === 'EXECUTED' || code === 'APPROVED_HITL') success++;
      else if (code === 'PENDING_HITL') pendingCount++;
      else if (code.startsWith('REJECTED') || code === 'SCHEMA_ABORT' || code === 'DENIED_HITL') rejected++;
    });
    return { success, pending: pendingCount, rejected };
  }, []);

  // ── Polling ───────────────────────────────────────────────────────────────
  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [healthRes, pendingRes, auditRes, portfolioRes] = await Promise.allSettled([
          axios.get(`${API_BASE}/health`),
          axios.get(`${API_BASE}/pending`),
          axios.get(`${API_BASE}/audit`),
          axios.get(`${API_BASE}/portfolio`),
        ]);
        if (healthRes.status === 'fulfilled')  setHealth(healthRes.value.data);
        if (pendingRes.status === 'fulfilled') setPending(pendingRes.value.data);
        if (auditRes.status === 'fulfilled')   setStats(buildStats(auditRes.value.data));
        if (portfolioRes.status === 'fulfilled') {
          const p = portfolioRes.value.data;
          setPortfolio(p);
          setPortfolioValue(calcPortfolioValue(p.holdings || []));
        }
        setLastRefresh(new Date());
      } catch (err) { console.error('Poll error:', err); }
    };
    fetchAll();
    const id = setInterval(fetchAll, 4000);
    return () => clearInterval(id);
  }, [buildStats, calcPortfolioValue]);

  // ── Persist to localStorage ───────────────────────────────────────────────
  useEffect(() => { saveSession(messages, tradeHistory, stats); }, [messages, tradeHistory, stats]);

  // ── Auto-scroll chat ──────────────────────────────────────────────────────
  useEffect(() => {
    if (activeTab === 'console') chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeTab]);

  // ── Send directive ────────────────────────────────────────────────────────
  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const prompt = inputValue;
    const userMsg = { role: 'user', content: prompt };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/execute`, { directive: prompt });
      const log = res.data;
      setMessages(prev => [...prev, { role: 'agent', log }]);
      // Add to trade history
      setTradeHistory(prev => [{
        id: log.log_id || Date.now(),
        session_id: log.session_id,
        submittedAt: log.event_timestamp_utc || new Date().toISOString(),
        prompt,
        decision_code: log.decision_code,
        ticker: log.ticker,
        action: log.action,
        estimated_value_usd: log.estimated_value_usd,
        consensus_match: log.consensus_match,
        policy_checks_passed: log.policy_checks_passed,
        policy_checks_failed: log.policy_checks_failed,
      }, ...prev]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'agent', error: 'Connection failed or server error.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  // ── HITL decision ─────────────────────────────────────────────────────────
  const handleDecision = async (sessionId, action) => {
    try {
      const res = await axios.post(`${API_BASE}/decision/${sessionId}`, { action });
      const finalCode = res.data.decision_code || (action === 'APPROVE' ? 'APPROVED_HITL' : 'DENIED_HITL');
      
      setPending(prev => prev.filter(p => p.session_id !== sessionId));
      
      // Update tradeHistory entry immediately
      setTradeHistory(prev => prev.map(t => 
        t.session_id === sessionId ? { ...t, decision_code: finalCode } : t
      ));

      // Update matching chat message immediately
      setMessages(prev => prev.map(m => {
        if (m.role === 'agent' && m.log && m.log.session_id === sessionId) {
          return { ...m, log: { ...m.log, decision_code: finalCode } };
        }
        return m;
      }));
    } catch (err) { console.error('Decision error:', err); }
  };

  const clearSession = () => {
    if (window.confirm('Clear all chat history and trade log?')) {
      localStorage.removeItem(STORAGE_KEY);
      setMessages([]);
      setTradeHistory([]);
      setStats({ success: 0, pending: 0, rejected: 0 });
    }
  };

  const pendingCount = pending.length;
  const totalTrades  = stats.success + stats.rejected + pendingCount;

  return (
    <div className="app-container">

      {/* ── HEADER ──────────────────────────────────────────────────────── */}
      <header className="header glass-panel">
        <div className="title-group">
          <ShieldCheck size={26} className="title-icon" />
          <div>
            <h1>Zero-Trust Trading Desk</h1>
            <p className="subtitle">Multi-Agent · HITL · Zero-Trust Architecture</p>
          </div>
        </div>
        <div className="header-right">
          {lastRefresh && (
            <span className="last-refresh"><RefreshCw size={11} />{lastRefresh.toLocaleTimeString()}</span>
          )}
          <div className="health-indicator">
            <Activity size={18} color={health.status === 'healthy' ? '#34d399' : '#fbbf24'} />
            <div className={`health-status ${health.status !== 'healthy' ? 'degraded' : ''}`}>
              {health.status === 'healthy' ? 'Healthy' : 'Unhealthy'}
            </div>
          </div>
        </div>
      </header>

      {/* ── STATS BAR ───────────────────────────────────────────────────── */}
      <div className="stats-bar">
        <StatCard icon={CheckCircle2} label="Executed" value={stats.success} color="#34d399"
          sublabel={totalTrades > 0 ? `${Math.round(stats.success / totalTrades * 100)}% rate` : '—'} />
        <StatCard icon={Clock} label="Pending HITL" value={pendingCount} color="#fbbf24" sublabel="Awaiting review" />
        <StatCard icon={Ban} label="Rejected" value={stats.rejected} color="#f87171"
          sublabel={totalTrades > 0 ? `${Math.round(stats.rejected / totalTrades * 100)}% rate` : '—'} />
        <StatCard icon={Wallet} label="Portfolio"
          value={`$${portfolioValue.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`}
          color="#818cf8" sublabel={`${portfolio.holdings.length} holding${portfolio.holdings.length !== 1 ? 's' : ''}`} />
        <StatCard icon={TrendingUp} label="Total Volume" value={totalTrades} color="#38bdf8" sublabel="All decisions" />
      </div>

      {/* ── MAIN GRID ───────────────────────────────────────────────────── */}
      <div className="main-grid">

        {/* ── LEFT: TABBED CONSOLE ──────────────────────────────────── */}
        <section className="console-section glass-panel">

          {/* Tab Bar */}
          <div className="tab-bar">
            <button
              className={`tab-btn ${activeTab === 'console' ? 'active' : ''}`}
              onClick={() => setActiveTab('console')}
            >
              <MessageSquare size={14} /> Console
            </button>
            <button
              className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => setActiveTab('history')}
            >
              <History size={14} /> Trade History
              {tradeHistory.length > 0 && <span className="tab-count">{tradeHistory.length}</span>}
            </button>
            <div style={{ flex: 1 }} />
            <button className="btn-ghost" onClick={clearSession} title="Clear all">
              <XCircle size={14} /> Clear
            </button>
          </div>

          {/* ── CONSOLE TAB ─────────────────────────────────────── */}
          {activeTab === 'console' && (
            <>
              <div className="chat-history">
                {messages.length === 0 && (
                  <div className="empty-state">
                    <ShieldCheck size={44} style={{ opacity: 0.35, marginBottom: '0.75rem' }} />
                    <p>System Ready. Enter a trading directive below.</p>
                    <p className="hint">Try: "Analyze AAPL. Both agents bullish. Trade value ~$750."</p>
                  </div>
                )}
                {messages.map((msg, i) => (
                  <div key={i} className={`message ${msg.role}`}>
                    {msg.role === 'user'
                      ? <div>{msg.content}</div>
                      : msg.error
                        ? <div style={{ color: 'var(--danger)' }}>{msg.error}</div>
                        : <EventLogCard log={msg.log} />
                    }
                  </div>
                ))}
                {isLoading && (
                  <div className="message agent loading-dots">
                    <div className="dot" /><div className="dot" /><div className="dot" />
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              <form className="input-area" onSubmit={handleSend}>
                <input
                  type="text"
                  placeholder="e.g., Analyze MSFT. Bullish signals. Propose a buy of 5 shares at $300."
                  value={inputValue}
                  onChange={e => setInputValue(e.target.value)}
                  disabled={isLoading}
                />
                <button type="submit" disabled={isLoading || !inputValue.trim()}>
                  <Send size={16} /> Send
                </button>
              </form>
            </>
          )}

          {/* ── TRADE HISTORY TAB ───────────────────────────────── */}
          {activeTab === 'history' && (
            <div className="trade-history-panel">
              {tradeHistory.length === 0 ? (
                <div className="empty-state">
                  <History size={44} style={{ opacity: 0.35, marginBottom: '0.75rem' }} />
                  <p>No trades recorded yet.</p>
                  <p className="hint">Submit a directive in the Console tab.</p>
                </div>
              ) : (
                tradeHistory.map((entry) => (
                  <TradeHistoryRow key={entry.id} entry={entry} />
                ))
              )}
            </div>
          )}

        </section>

        {/* ── RIGHT SIDEBAR ─────────────────────────────────────────── */}
        <aside className="right-sidebar">

          {/* HITL Queue */}
          <div className="hitl-panel glass-panel">
            <h2>
              <AlertTriangle size={16} /> HITL Review Queue
              {pendingCount > 0 && <span className="badge-count">{pendingCount}</span>}
            </h2>
            <div className="hitl-list">
              {pendingCount === 0 ? (
                <div className="empty-queue">
                  <CheckCircle2 size={18} style={{ opacity: 0.5 }} />
                  <span>No pending trades</span>
                </div>
              ) : (
                pending.map(p => (
                  <div key={p.session_id} className="hitl-card">
                    <div className="hitl-ticker">
                      <span className="hitl-action-badge">{p.proposal_summary.action}</span>
                      <span className="hitl-ticker-name">{p.proposal_summary.ticker}</span>
                    </div>
                    <div className="hitl-details">
                      <DollarSign size={12} />
                      ${(p.proposal_summary.estimated_value_usd || 0).toFixed(2)}
                    </div>
                    {p.proposal_summary.vibe_diff && (
                      <div className="hitl-vibe-diff">
                        <span className="vibe-label">Thesis</span>
                        {p.proposal_summary.vibe_diff}
                      </div>
                    )}
                    <div className="hitl-actions">
                      <button className="btn-approve" onClick={() => handleDecision(p.session_id, 'APPROVE')}>
                        <CheckCircle2 size={13} /> Approve
                      </button>
                      <button className="btn-deny" onClick={() => handleDecision(p.session_id, 'DENY')}>
                        <XCircle size={13} /> Deny
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Portfolio Holdings */}
          <div className="portfolio-panel glass-panel">
            <h2><Wallet size={16} /> Portfolio Holdings</h2>
            <div className="portfolio-list">
              {portfolio.holdings.length === 0 ? (
                <div className="empty-queue"><span>No holdings data</span></div>
              ) : (
                portfolio.holdings.map((h, i) => (
                  <div key={i} className="holding-row">
                    <div className="holding-symbol">{h.tradingsymbol}</div>
                    <div className="holding-details">
                      <span>{h.quantity} sh @ ${h.average_price}</span>
                      <span className="holding-value">
                        ${(h.quantity * h.average_price).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

        </aside>
      </div>
    </div>
  );
}

export default App;
