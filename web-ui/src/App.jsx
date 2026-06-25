import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { ShieldCheck, Activity, Send, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8004/api';

function App() {
  const [health, setHealth] = useState({ composite_score: 1.0, status: 'healthy' });
  const [pending, setPending] = useState([]);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Polling for health and pending queue
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [healthRes, pendingRes] = await Promise.all([
          axios.get(`${API_BASE}/health`),
          axios.get(`${API_BASE}/pending`)
        ]);
        setHealth(healthRes.data);
        setPending(pendingRes.data);
      } catch (err) {
        console.error("Error fetching state:", err);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMsg = { role: 'user', content: inputValue };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/execute`, { directive: userMsg.content });
      setMessages(prev => [...prev, { role: 'agent', log: res.data }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'agent', error: 'Connection failed or server error.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDecision = async (sessionId, action) => {
    try {
      await axios.post(`${API_BASE}/decision/${sessionId}`, { action });
      // optimistic update
      setPending(prev => prev.filter(p => p.session_id !== sessionId));
    } catch (err) {
      console.error("Error submitting decision:", err);
    }
  };

  return (
    <div className="app-container">
      {/* HEADER */}
      <header className="header glass-panel">
        <div className="title-group">
          <h1>Zero-Trust Trading Desk</h1>
        </div>
        <div className="health-indicator">
          <Activity size={20} color={health.status === 'healthy' ? '#34d399' : '#fbbf24'} />
          <div className="health-score">{(health.composite_score * 100).toFixed(1)}%</div>
          <div className={`health-status ${health.status === 'degraded' ? 'degraded' : ''}`}>
            {health.status}
          </div>
        </div>
      </header>

      {/* MAIN GRID */}
      <div className="main-grid">
        
        {/* CONSOLE */}
        <section className="console-section glass-panel">
          <div className="chat-history">
            {messages.length === 0 && (
              <div style={{color: 'var(--text-secondary)', textAlign: 'center', marginTop: '2rem'}}>
                <ShieldCheck size={48} style={{opacity: 0.5, marginBottom: '1rem'}} />
                <p>System Ready. Enter a trading directive to begin.</p>
              </div>
            )}
            
            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`}>
                {msg.role === 'user' ? (
                  <div>{msg.content}</div>
                ) : (
                  msg.error ? (
                    <div style={{color: 'var(--danger)'}}>{msg.error}</div>
                  ) : (
                    <EventLogCard log={msg.log} />
                  )
                )}
              </div>
            ))}
            
            {isLoading && (
              <div className="message agent loading-dots">
                <div className="dot"></div><div className="dot"></div><div className="dot"></div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>
          
          <form className="input-area" onSubmit={handleSend}>
            <input 
              type="text" 
              placeholder="e.g., Analyze AAPL. Both agents bullish. Trade value ~$750." 
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              disabled={isLoading}
            />
            <button type="submit" disabled={isLoading || !inputValue.trim()}>
              <Send size={18} /> Send
            </button>
          </form>
        </section>

        {/* HITL QUEUE */}
        <aside className="hitl-panel glass-panel">
          <h2><AlertTriangle size={20} /> HITL Review Queue</h2>
          <div className="hitl-list">
            {pending.length === 0 ? (
              <div style={{color: 'var(--text-secondary)', fontSize: '0.9rem'}}>No pending trades.</div>
            ) : (
              pending.map(p => (
                <div key={p.session_id} className="hitl-card">
                  <h3>{p.proposal_summary.action} {p.proposal_summary.ticker}</h3>
                  <div className="hitl-details">
                    Est. Value: ${p.proposal_summary.estimated_value_usd.toFixed(2)}
                  </div>
                  <div className="hitl-actions">
                    <button className="btn-approve" onClick={() => handleDecision(p.session_id, 'APPROVE')}>
                      Approve
                    </button>
                    <button className="btn-deny" onClick={() => handleDecision(p.session_id, 'DENY')}>
                      Deny
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}

function EventLogCard({ log }) {
  const isRejected = log.decision_code.startsWith('REJECTED') || log.decision_code === 'SCHEMA_ABORT';
  const isPending = log.decision_code === 'PENDING_HITL';
  
  const badgeClass = isRejected ? 'decision-REJECTED' : 
                     isPending ? 'decision-PENDING_HITL' : 'decision-EXECUTED';

  return (
    <div className="event-log-card">
      <div className="event-log-header">
        <span style={{fontWeight: 600}}>System Decision</span>
        <span className={`decision-badge ${badgeClass}`}>{log.decision_code}</span>
      </div>
      <div style={{marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between'}}>
        <span>{log.action} {log.ticker}</span>
        <span>${log.estimated_value_usd.toFixed(2)}</span>
      </div>
      
      <ul className="check-list">
        <li>
          {log.consensus_match ? <CheckCircle2 size={16} className="passed"/> : <XCircle size={16} className="failed"/>}
          Consensus: {log.consensus_match ? 'Matched' : 'Conflict'}
        </li>
        {log.policy_checks_passed.map(check => (
          <li key={check}>
            <CheckCircle2 size={16} className="passed"/> Policy: {check} OK
          </li>
        ))}
        {log.policy_checks_failed.map(check => (
          <li key={check}>
            <XCircle size={16} className="failed"/> Policy: {check} FAILED
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
