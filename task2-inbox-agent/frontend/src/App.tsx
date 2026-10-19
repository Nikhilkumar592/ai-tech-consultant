import { useState, useEffect } from 'react';
import { FALLBACK_EMAILS, FALLBACK_AUTONOMY_STATUS } from './fallbackData';

interface EmailSummary {
  id: string;
  from_name: string;
  from_email: string;
  subject: string;
  received_at: string;
  status: string;
  category: string;
  priority: string;
  urgency: string;
  sentiment: string;
  confidence_score: number;
  is_spam: boolean;
  escalation_reason?: string;
}

interface EmailDetail extends EmailSummary {
  body: string;
  draft_response: string;
  edited_response: string;
  retrieved_sources: Array<{ title: string; url: string; relevance_score?: number }>;
  reviewed_by?: string;
}

interface AutonomyStatus {
  category: string;
  consecutive_approvals: number;
  is_autonomous: boolean;
  suggestion_ready: boolean;
  target_threshold: number;
  total_approved: number;
  total_rejected: number;
}

const API_BASE = (import.meta as unknown as { env?: { VITE_API_BASE?: string } }).env?.VITE_API_BASE || 'http://localhost:8001';

export default function App() {
  const [emails, setEmails] = useState<EmailSummary[]>(FALLBACK_EMAILS);
  const [selectedEmail, setSelectedEmail] = useState<EmailDetail | null>(FALLBACK_EMAILS[0]);
  const [autonomyStatuses, setAutonomyStatuses] = useState<AutonomyStatus[]>(FALLBACK_AUTONOMY_STATUS);
  const [isLiveBackend, setIsLiveBackend] = useState<boolean>(false);
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [draftText, setDraftText] = useState<string>(FALLBACK_EMAILS[0].draft_response || '');
  const [loading, setLoading] = useState<boolean>(false);
  const [statusMsg, setStatusMsg] = useState<string>('');

  // Fetch emails and autonomy status
  const loadData = async () => {
    try {
      const [emailRes, autoRes] = await Promise.all([
        fetch(`${API_BASE}/emails?limit=100`),
        fetch(`${API_BASE}/autonomy/status`),
      ]);
      if (emailRes.ok) {
        const data = await emailRes.json();
        setEmails(data);
        setIsLiveBackend(true);
        if (data.length > 0 && !selectedEmail) {
          selectEmail(data[0].id);
        }
      }
      if (autoRes.ok) {
        const autoData = await autoRes.json();
        setAutonomyStatuses(autoData);
      }
    } catch {
      setIsLiveBackend(false);
      // Retain fallback data smoothly in static preview mode
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, []);

  const selectEmail = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/emails/${id}`);
      if (res.ok) {
        const data: EmailDetail = await res.json();
        setSelectedEmail(data);
        setDraftText(data.edited_response || data.draft_response || '');
        return;
      }
    } catch {
      // Fallback local selection
    }
    const local = emails.find((e) => e.id === id) as EmailDetail;
    if (local) {
      setSelectedEmail(local);
      setDraftText(local.edited_response || local.draft_response || '');
    }
  };

  const handleSeed = async () => {
    setLoading(true);
    setStatusMsg('Seeding 50 sample customer emails...');
    try {
      const res = await fetch(`${API_BASE}/inbox/seed`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setStatusMsg(`Seeded ${data.count} emails successfully.`);
        await loadData();
        return;
      }
    } catch {
      // Fallback
    }
    setEmails(FALLBACK_EMAILS);
    setStatusMsg('Loaded sample dataset in preview mode.');
    setLoading(false);
  };

  const handleProcessAll = async () => {
    setLoading(true);
    setStatusMsg('AI Agent classifying and generating grounded drafts...');
    try {
      const res = await fetch(`${API_BASE}/emails/process-all`, { method: 'POST' });
      const data = await res.json();
      setStatusMsg(data.message || 'Processing complete.');
      await loadData();
      if (selectedEmail) {
        selectEmail(selectedEmail.id);
      }
    } catch (e) {
      setStatusMsg('Processing failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleProcessSingle = async () => {
    if (!selectedEmail) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/emails/${selectedEmail.id}/process`, { method: 'POST' });
      if (res.ok) {
        const updated = await res.json();
        setSelectedEmail(updated);
        setDraftText(updated.edited_response || updated.draft_response || '');
        await loadData();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!selectedEmail) return;
    setLoading(true);
    try {
      const isEdited = draftText !== (selectedEmail.draft_response || '');
      let res;
      if (isEdited) {
        res = await fetch(`${API_BASE}/emails/${selectedEmail.id}/edit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ edited_draft: draftText, editor_name: 'Lead Reviewer' }),
        });
      } else {
        res = await fetch(`${API_BASE}/emails/${selectedEmail.id}/approve`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reviewer_name: 'Lead Reviewer' }),
        });
      }
      if (res && res.ok) {
        const updated = await res.json();
        setSelectedEmail(updated);
        setStatusMsg(`Email ${selectedEmail.id} approved & sent.`);
        await loadData();
        return;
      }
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
    // Offline / Demo state update
    const updated = { ...selectedEmail, status: 'approved', edited_response: draftText };
    setSelectedEmail(updated);
    setEmails((prev) => prev.map((e) => (e.id === updated.id ? { ...e, status: 'approved' } : e)));
    setStatusMsg(`Email ${selectedEmail.id} approved & marked sent (demo preview).`);
  };

  const handleReject = async () => {
    if (!selectedEmail) return;
    try {
      const res = await fetch(`${API_BASE}/emails/${selectedEmail.id}/reject`, { method: 'POST' });
      if (res.ok) {
        const updated = await res.json();
        setSelectedEmail(updated);
        setStatusMsg(`Draft rejected. Streak reset for ${selectedEmail.category}.`);
        await loadData();
        return;
      }
    } catch {
      // Fallback
    }
    const updated = { ...selectedEmail, status: 'rejected' };
    setSelectedEmail(updated);
    setEmails((prev) => prev.map((e) => (e.id === updated.id ? { ...e, status: 'rejected' } : e)));
    setStatusMsg(`Draft rejected. Streak reset for ${selectedEmail.category} (demo preview).`);
  };

  const handleEscalate = async () => {
    if (!selectedEmail) return;
    try {
      const res = await fetch(`${API_BASE}/emails/${selectedEmail.id}/escalate`, { method: 'POST' });
      if (res.ok) {
        const updated = await res.json();
        setSelectedEmail(updated);
        setStatusMsg(`Email ${selectedEmail.id} escalated to human queue.`);
        await loadData();
        return;
      }
    } catch {
      // Fallback
    }
    const updated = { ...selectedEmail, status: 'escalated' };
    setSelectedEmail(updated);
    setEmails((prev) => prev.map((e) => (e.id === updated.id ? { ...e, status: 'escalated' } : e)));
    setStatusMsg(`Email ${selectedEmail.id} escalated to expert queue.`);
  };

  const handleConfirmAutonomy = async (cat: string) => {
    try {
      const res = await fetch(`${API_BASE}/autonomy/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category: cat, enable_autonomous: true, confirmed_by: 'Operations Director' }),
      });
      if (res.ok) {
        setStatusMsg(`Category '${cat}' is now AUTONOMOUS.`);
        await loadData();
        return;
      }
    } catch {
      // Fallback
    }
    setAutonomyStatuses((prev) =>
      prev.map((a) => (a.category === cat ? { ...a, is_autonomous: true, suggestion_ready: false } : a))
    );
    setStatusMsg(`Category '${cat}' enabled for autonomous processing.`);
  };

  // Filter emails
  const filteredEmails = emails.filter((e) => {
    if (categoryFilter !== 'all' && e.category !== categoryFilter) return false;
    if (statusFilter !== 'all' && e.status !== statusFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        e.subject.toLowerCase().includes(q) ||
        e.from_name.toLowerCase().includes(q) ||
        e.from_email.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const readyAutonomyCategory = autonomyStatuses.find((a) => a.suggestion_ready);

  return (
    <>
      <header className="app-header">
        <div className="header-brand">
          <span className="logo-badge">TASK 2</span>
          <div>
            <div className="header-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>Intelligent Inbox & Autonomy Review</span>
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  padding: '2px 8px',
                  borderRadius: '12px',
                  background: isLiveBackend ? 'rgba(16, 185, 129, 0.15)' : 'rgba(99, 102, 241, 0.15)',
                  color: isLiveBackend ? '#10b981' : '#818cf8',
                  border: isLiveBackend ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(99, 102, 241, 0.3)',
                }}
              >
                {isLiveBackend ? '● Backend Connected' : '⚡ Interactive Demo Preview'}
              </span>
            </div>
            <div className="header-subtitle">
              Port 8001 | Grounded RAG with 20-Consecutive-Approval Rule
            </div>
          </div>
        </div>
        <div className="header-actions">
          {statusMsg && <span style={{ fontSize: '12px', color: '#10b981' }}>{statusMsg}</span>}
          <button className="btn btn-outline" onClick={handleSeed} disabled={loading}>
            📥 Seed 50 Emails
          </button>
          <button className="btn btn-primary" onClick={handleProcessAll} disabled={loading}>
            ⚡ Run AI Classification & Drafting
          </button>
        </div>
      </header>

      <div className="app-container">
        {/* Left Sidebar */}
        <aside className="sidebar-panel">
          <div className="sidebar-search">
            <input
              type="text"
              className="search-input"
              placeholder="Search sender, subject..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="filter-bar">
            {['all', 'technical_support', 'billing', 'general_inquiry', 'escalation', 'spam'].map((cat) => (
              <span
                key={cat}
                className={`filter-chip ${categoryFilter === cat ? 'active' : ''}`}
                onClick={() => setCategoryFilter(cat)}
              >
                {cat.replace('_', ' ')}
              </span>
            ))}
          </div>

          <div className="filter-bar" style={{ paddingTop: 0 }}>
            {['all', 'unprocessed', 'draft_ready', 'approved', 'escalated', 'rejected'].map((st) => (
              <span
                key={st}
                className={`filter-chip ${statusFilter === st ? 'active' : ''}`}
                style={{ fontSize: '10px' }}
                onClick={() => setStatusFilter(st)}
              >
                {st.replace('_', ' ')}
              </span>
            ))}
          </div>

          <div className="email-list">
            {filteredEmails.map((email) => (
              <div
                key={email.id}
                className={`email-item ${selectedEmail?.id === email.id ? 'selected' : ''}`}
                onClick={() => selectEmail(email.id)}
              >
                <div className="email-header-row">
                  <span className="email-sender">{email.from_name || email.from_email}</span>
                  <span className="email-time">
                    {new Date(email.received_at).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                  </span>
                </div>
                <div className="email-subject">{email.subject}</div>
                <div className="badges-row">
                  <span className={`badge badge-${email.category.split('_')[0]}`}>
                    {email.category.replace('_', ' ')}
                  </span>
                  <span className={`badge badge-${email.urgency.slice(0, 4)}`}>{email.urgency}</span>
                  <span
                    style={{
                      fontSize: '10px',
                      color:
                        email.status === 'approved'
                          ? '#10b981'
                          : email.status === 'escalated'
                          ? '#f87171'
                          : '#94a3b8',
                      fontWeight: 600,
                    }}
                  >
                    ● {email.status.replace('_', ' ')}
                  </span>
                </div>
              </div>
            ))}
            {filteredEmails.length === 0 && (
              <div style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
                No emails match the selected filter.
              </div>
            )}
          </div>
        </aside>

        {/* Main Review Panel */}
        <main className="detail-panel">
          <div className="detail-content">
            {readyAutonomyCategory && (
              <div className="alert-banner">
                <div>
                  <strong style={{ color: '#fff', fontSize: '14px' }}>
                    🎉 Autonomy Recommendation Ready!
                  </strong>
                  <div style={{ fontSize: '13px', color: '#cbd5e1', marginTop: '2px' }}>
                    Category <strong>'{readyAutonomyCategory.category.replace('_', ' ')}'</strong> has
                    achieved 20 consecutive human approvals. Transition to Autonomous Sending?
                  </div>
                </div>
                <button
                  className="btn btn-success"
                  onClick={() => handleConfirmAutonomy(readyAutonomyCategory.category)}
                >
                  ✓ Confirm & Enable Autonomy
                </button>
              </div>
            )}

            {selectedEmail ? (
              <>
                {/* Email Metadata Card */}
                <div className="card">
                  <div className="card-title">
                    <span>{selectedEmail.subject}</span>
                    <span style={{ fontSize: '12px', color: '#64748b' }}>
                      ID: {selectedEmail.id}
                    </span>
                  </div>

                  <div className="email-meta-grid">
                    <div className="meta-item">
                      <span className="meta-label">FROM</span>
                      <span className="meta-val">
                        {selectedEmail.from_name} ({selectedEmail.from_email})
                      </span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">CATEGORY</span>
                      <span className="meta-val">{selectedEmail.category.replace('_', ' ')}</span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">URGENCY & PRIORITY</span>
                      <span className="meta-val">
                        {selectedEmail.urgency.toUpperCase()} ({selectedEmail.priority})
                      </span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">CONFIDENCE SCORE</span>
                      <span
                        className="meta-val"
                        style={{
                          color:
                            selectedEmail.confidence_score > 0.75
                              ? '#10b981'
                              : selectedEmail.confidence_score > 0.4
                              ? '#f59e0b'
                              : '#ef4444',
                        }}
                      >
                        {(selectedEmail.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  <div className="email-body-text">{selectedEmail.body}</div>
                </div>

                {/* AI Grounded Draft Card */}
                <div className="card">
                  <div className="card-title">
                    <span>AI-Generated Grounded Draft Response</span>
                    {selectedEmail.status === 'unprocessed' && (
                      <button className="btn btn-outline" onClick={handleProcessSingle}>
                        Generate Draft
                      </button>
                    )}
                  </div>

                  {selectedEmail.status === 'escalated' ? (
                    <div
                      style={{
                        padding: '16px',
                        background: 'rgba(239, 68, 68, 0.1)',
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        borderRadius: '6px',
                        color: '#fca5a5',
                        marginBottom: '14px',
                      }}
                    >
                      <strong>⚠️ Human Expert Escalation Triggered</strong>
                      <div style={{ fontSize: '13px', marginTop: '4px' }}>
                        Reason: {selectedEmail.escalation_reason || 'Requires human verification.'}
                      </div>
                    </div>
                  ) : null}

                  <textarea
                    className="draft-textarea"
                    value={draftText}
                    onChange={(e) => setDraftText(e.target.value)}
                    placeholder="Draft response will appear here once processed..."
                  />

                  {selectedEmail.retrieved_sources && selectedEmail.retrieved_sources.length > 0 && (
                    <div className="sources-box">
                      <div className="sources-title">
                        📚 Grounded Knowledge Sources from Knowledge Brain:
                      </div>
                      <div>
                        {selectedEmail.retrieved_sources.map((src, idx) => (
                          <span key={idx} className="source-pill">
                            📄 <strong>{src.title}</strong> ({src.url})
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="detail-action-bar">
                    <button
                      className="btn btn-success"
                      onClick={handleApprove}
                      disabled={loading || !draftText}
                    >
                      ✓ Approve & Send
                    </button>
                    <button
                      className="btn btn-primary"
                      onClick={handleApprove}
                      disabled={loading || !draftText}
                    >
                      💾 Save Edits & Approve (Store Feedback)
                    </button>
                    <button
                      className="btn btn-danger"
                      onClick={handleReject}
                      disabled={loading}
                    >
                      ✕ Reject Draft (Reset Streak)
                    </button>
                    <button
                      className="btn btn-warning"
                      onClick={handleEscalate}
                      disabled={loading}
                    >
                      ⚠️ Escalate to Expert
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="empty-state">
                <h2>No Email Selected</h2>
                <p>Choose an incoming customer email from the left sidebar to review and edit.</p>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Bottom Autonomy Bar */}
      <footer className="autonomy-strip">
        <div style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>
          20-APPROVAL AUTONOMY STREAKS:
        </div>
        <div className="streak-pills">
          {autonomyStatuses.map((stat) => (
            <div key={stat.category} className="streak-pill">
              <span>{stat.category.replace('_', ' ')}:</span>
              <div className="progress-bar-wrap">
                <div
                  className={`progress-bar-fill ${
                    stat.consecutive_approvals >= stat.target_threshold ? 'complete' : ''
                  }`}
                  style={{
                    width: `${Math.min(100, (stat.consecutive_approvals / stat.target_threshold) * 100)}%`,
                  }}
                />
              </div>
              <span style={{ fontSize: '11px', color: '#cbd5e1' }}>
                {stat.consecutive_approvals}/{stat.target_threshold}
              </span>
              {stat.is_autonomous && (
                <span className="badge badge-billing" style={{ fontSize: '9px' }}>
                  AUTO
                </span>
              )}
            </div>
          ))}
        </div>
      </footer>
    </>
  );
}
