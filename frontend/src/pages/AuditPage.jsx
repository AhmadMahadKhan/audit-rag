import React, { useState, useEffect, useRef, useCallback } from 'react';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Spinner from '../components/common/Spinner';
import Toast from '../components/common/Toast';
import Modal from '../components/common/Modal';
import { listAuditRuns, startAudit, getAuditRun, getAuditMemoryTrail, getAuditReport, downloadAuditReportPdf } from '../api/audit';
import { listDocuments } from '../api/documents';
import {
  ShieldCheck,
  Plus,
  FileText,
  CheckSquare,
  Square,
  AlertTriangle,
  Loader2,
  Clock,
  FileWarning,
  ListChecks,
  HelpCircle,
  ChevronRight,
  Download
} from 'lucide-react';

const POLL_INTERVAL_MS = 3000;

const statusVariant = (status) => {
  if (status === 'completed') return 'success';
  if (status === 'failed') return 'danger';
  if (status === 'running') return 'warning';
  return 'info';
};

const severityVariant = (severity) => {
  if (severity === 'critical') return 'danger';
  if (severity === 'high') return 'danger';
  if (severity === 'medium') return 'warning';
  return 'info';
};

export const AuditPage = () => {
  const [runs, setRuns] = useState([]);
  const [activeRunId, setActiveRunId] = useState(null);
  const [activeRun, setActiveRun] = useState(null);
  const [snapshots, setSnapshots] = useState([]);
  const [report, setReport] = useState(null);
  const [loadingRuns, setLoadingRuns] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [isNewAuditOpen, setIsNewAuditOpen] = useState(false);
  const pollRef = useRef(null);

  const addToast = (message, type = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  };

  const fetchRuns = useCallback(() => {
    setLoadingRuns(true);
    listAuditRuns()
      .then((data) => {
        setRuns(data);
        setLoadingRuns(false);
        if (!activeRunId && data.length > 0) {
          setActiveRunId(data[0].id);
        }
      })
      .catch(() => {
        addToast('Failed to load audit runs', 'error');
        setLoadingRuns(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    fetchRuns();
  }, [fetchRuns]);

  // Load / poll the active run's detail + memory trail
  useEffect(() => {
    if (!activeRunId) {
      setActiveRun(null);
      setSnapshots([]);
      setReport(null);
      return;
    }

    let cancelled = false;

    const loadDetail = async (showSpinner) => {
      if (showSpinner) setLoadingDetail(true);
      try {
        const [run, trail] = await Promise.all([
          getAuditRun(activeRunId),
          getAuditMemoryTrail(activeRunId)
        ]);
        if (cancelled) return;
        setActiveRun(run);
        setSnapshots(trail);

        if (run.status === 'completed') {
          try {
            const rep = await getAuditReport(activeRunId);
            if (!cancelled) setReport(rep);
          } catch {
            // report not ready yet despite status - will retry on next poll
          }
        } else {
          setReport(null);
        }
      } catch (err) {
        if (!cancelled) addToast('Failed to load audit run details', 'error');
      } finally {
        if (!cancelled && showSpinner) setLoadingDetail(false);
      }
    };

    loadDetail(true);
    if (pollRef.current) clearInterval(pollRef.current);

    pollRef.current = setInterval(() => {
      loadDetail(false);
    }, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [activeRunId]);

  // Stop polling once the run is done
  useEffect(() => {
    if (activeRun && (activeRun.status === 'completed' || activeRun.status === 'failed')) {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    }
  }, [activeRun]);

  const handleAuditStarted = (newRun) => {
    setRuns((prev) => [newRun, ...prev]);
    setActiveRunId(newRun.id);
    setIsNewAuditOpen(false);
    addToast('Audit run started', 'success');
  };

  const progressPct = activeRun && activeRun.progress_total > 0
    ? Math.round((activeRun.progress_current / activeRun.progress_total) * 100)
    : 0;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '20px', height: 'calc(100vh - 120px)' }}>
      {/* Left Sidebar: Runs list */}
      <Card style={{ display: 'flex', flexDirection: 'column', padding: '16px' }}>
        <button
          className="btn btn-primary"
          onClick={() => setIsNewAuditOpen(true)}
          style={{ width: '100%', marginBottom: '16px', justifyContent: 'center' }}
        >
          <Plus size={16} />
          <span>New Audit Run</span>
        </button>

        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.05em' }}>
          Audit Runs
        </div>

        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {loadingRuns ? (
            <div style={{ padding: '30px', textAlign: 'center' }}>
              <Spinner size={24} />
            </div>
          ) : runs.length === 0 ? (
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', padding: '8px' }}>
              No audit runs yet. Start one to see AI-generated insights.
            </p>
          ) : (
            runs.map((run) => {
              const isActive = run.id === activeRunId;
              return (
                <div
                  key={run.id}
                  onClick={() => setActiveRunId(run.id)}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: isActive ? 'var(--primary-subtle)' : 'var(--bg-surface)',
                    border: `1px solid ${isActive ? 'var(--primary)' : 'transparent'}`,
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0, marginBottom: '6px' }}>
                    <ShieldCheck size={16} style={{ color: isActive ? 'var(--primary)' : 'var(--text-muted)', flexShrink: 0 }} />
                    <span style={{
                      fontSize: '0.8125rem',
                      fontWeight: isActive ? 600 : 500,
                      color: isActive ? 'var(--primary)' : 'var(--text-primary)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {run.name}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Badge variant={statusVariant(run.status)}>{run.status}</Badge>
                    {run.status === 'running' && (
                      <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                        {run.progress_current}/{run.progress_total}
                      </span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </Card>

      {/* Right: Active run detail */}
      <Card style={{ display: 'flex', flexDirection: 'column', padding: '0', overflow: 'hidden' }}>
        {!activeRunId ? (
          <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)', margin: 'auto' }}>
            <ShieldCheck size={36} style={{ margin: '0 auto 12px', color: 'var(--primary)' }} />
            <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>No Audit Run Selected</p>
            <p style={{ fontSize: '0.8125rem', marginTop: '4px' }}>Start a new audit run to have the AI agent review your documents.</p>
          </div>
        ) : loadingDetail && !activeRun ? (
          <div style={{ padding: '80px', textAlign: 'center', margin: 'auto' }}>
            <Spinner size={32} />
          </div>
        ) : activeRun ? (
          <>
            {/* Header */}
            <div style={{
              padding: '16px 20px',
              borderBottom: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor: 'var(--bg-glass)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <ShieldCheck size={20} style={{ color: 'var(--primary)' }} />
                <div>
                  <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>{activeRun.name}</h3>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Started {new Date(activeRun.created_at).toLocaleString()}
                  </span>
                </div>
              </div>
              <Badge variant={statusVariant(activeRun.status)}>{activeRun.status}</Badge>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Progress / error banner while running or failed */}
              {activeRun.status === 'running' && (
                <div style={{
                  padding: '16px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                    <Loader2 size={16} className="spin" style={{ color: 'var(--primary)' }} />
                    <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>
                      {activeRun.current_stage || 'Processing'}...
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
                      {activeRun.progress_current} / {activeRun.progress_total} documents
                    </span>
                  </div>
                  <div style={{ height: '8px', width: '100%', backgroundColor: 'var(--bg-card)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{
                      height: '100%',
                      width: `${progressPct}%`,
                      backgroundColor: 'var(--primary)',
                      transition: 'width 0.4s ease'
                    }} />
                  </div>
                </div>
              )}

              {activeRun.status === 'failed' && (
                <div style={{
                  padding: '16px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'rgba(244, 63, 94, 0.08)',
                  border: '1px solid rgba(244, 63, 94, 0.25)',
                  display: 'flex',
                  gap: '10px'
                }}>
                  <FileWarning size={18} style={{ color: 'var(--accent-rose)', flexShrink: 0 }} />
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>Audit run failed</div>
                    <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {activeRun.error_message || 'An unknown error occurred during the audit run.'}
                    </div>
                  </div>
                </div>
              )}

              {/* Final report, once completed */}
              {activeRun.status === 'completed' && report && (
                <ReportView report={report} addToast={addToast} />
              )}

              {/* Live memory trail - always shown while snapshots exist */}
              {snapshots.length > 0 && (
                <div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '10px', letterSpacing: '0.05em' }}>
                    Document-by-Document Memory Trail
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {snapshots
                      .slice()
                      .sort((a, b) => a.order_index - b.order_index)
                      .map((snap) => (
                        <div
                          key={`${snap.document_id}-${snap.order_index}`}
                          style={{
                            padding: '14px 16px',
                            backgroundColor: 'var(--bg-surface)',
                            borderRadius: 'var(--radius-sm)',
                            border: '1px solid var(--border-subtle)'
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                            <span style={{
                              width: '20px', height: '20px', borderRadius: '50%',
                              backgroundColor: 'var(--primary-subtle)', color: 'var(--primary)',
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                              fontSize: '0.6875rem', fontWeight: 700, flexShrink: 0
                            }}>
                              {snap.order_index + 1}
                            </span>
                            <FileText size={14} style={{ color: 'var(--text-muted)' }} />
                            <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>{snap.document_id}</span>
                            {snap.memory_compacted && (
                              <Badge variant="purple">memory compacted</Badge>
                            )}
                            <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
                              {snap.map_batches_used} batch{snap.map_batches_used !== 1 ? 'es' : ''}
                            </span>
                          </div>
                          <p style={{ fontSize: '0.8125rem', lineHeight: 1.6, color: 'var(--text-secondary)' }}>
                            {snap.document_summary}
                          </p>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {activeRun.status !== 'failed' && snapshots.length === 0 && (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <Clock size={28} style={{ margin: '0 auto 10px' }} />
                  <p style={{ fontSize: '0.8125rem' }}>Waiting for the agent to begin processing documents...</p>
                </div>
              )}
            </div>
          </>
        ) : null}
      </Card>

      <NewAuditModal
        isOpen={isNewAuditOpen}
        onClose={() => setIsNewAuditOpen(false)}
        onStarted={handleAuditStarted}
        addToast={addToast}
      />

      <Toast toasts={toasts} onDismiss={(id) => setToasts((prev) => prev.filter((t) => t.id !== id))} />
    </div>
  );
};

const ReportView = ({ report, addToast }) => {
  const [downloading, setDownloading] = useState(false);
  const riskEntries = Object.entries(report.risk_summary || {});

  const handleDownload = async () => {
    setDownloading(true);
    try {
      await downloadAuditReportPdf(report.run_id, `audit-report-${report.run_id.slice(0, 8)}.pdf`);
    } catch {
      if (addToast) addToast('Failed to download PDF', 'error');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '12px' }}>
        <button className="btn btn-secondary" onClick={handleDownload} disabled={downloading}>
          {downloading ? <Spinner size={16} /> : <Download size={16} />}
          <span>Download PDF</span>
        </button>
      </div>

      <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <div style={{ padding: '10px 14px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>Documents Covered</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{report.documents_covered}</div>
        </div>
        {report.documents_failed > 0 && (
          <div style={{ padding: '10px 14px', borderRadius: 'var(--radius-sm)', backgroundColor: 'rgba(244, 63, 94, 0.08)', border: '1px solid rgba(244, 63, 94, 0.25)' }}>
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>Documents Failed</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-rose)' }}>{report.documents_failed}</div>
          </div>
        )}
        {riskEntries.map(([severity, count]) => (
          <div key={severity} style={{ padding: '10px 14px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>{severity}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: 700 }}>{count}</span>
              <Badge variant={severityVariant(severity)}>&nbsp;</Badge>
            </div>
          </div>
        ))}
      </div>

      <div style={{
        padding: '20px',
        backgroundColor: 'var(--bg-surface)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-subtle)',
        fontSize: '0.875rem',
        lineHeight: 1.7,
        whiteSpace: 'pre-wrap'
      }}>
        {report.content_markdown}
      </div>
    </div>
  );
};

const NewAuditModal = ({ isOpen, onClose, onStarted, addToast }) => {
  const [name, setName] = useState('');
  const [documents, setDocuments] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setName(`Audit — ${new Date().toLocaleDateString()}`);
      setSelectedIds([]);
      setLoadingDocs(true);
      listDocuments()
        .then((data) => {
          setDocuments(data);
          setLoadingDocs(false);
        })
        .catch(() => {
          addToast('Failed to load documents', 'error');
          setLoadingDocs(false);
        });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  const toggleDoc = (docId) => {
    setSelectedIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  const toggleAll = () => {
    if (selectedIds.length === documents.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(documents.map((d) => d.id));
    }
  };

  const handleStart = async () => {
    if (!name.trim()) {
      addToast('Please give this audit run a name', 'error');
      return;
    }
    setStarting(true);
    try {
      // Empty selection = audit every document you're authorized to see (per backend contract)
      const documentIds = selectedIds.length > 0 ? selectedIds : null;
      const run = await startAudit(name.trim(), documentIds);
      onStarted(run);
    } catch (err) {
      addToast('Failed to start audit run', 'error');
    } finally {
      setStarting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Start New Audit Run"
      maxWidth="560px"
      footer={
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button className="btn btn-secondary" onClick={onClose} disabled={starting}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={handleStart} disabled={starting}>
            {starting ? <Spinner size={16} /> : <ShieldCheck size={16} />}
            <span>Start Audit</span>
          </button>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div>
          <label style={{ fontSize: '0.8125rem', fontWeight: 600, marginBottom: '6px', display: 'block' }}>
            Audit Run Name
          </label>
          <input
            type="text"
            className="form-input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Q3 Compliance Review"
          />
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <label style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
              Select Documents
            </label>
            {documents.length > 0 && (
              <button
                onClick={toggleAll}
                style={{ fontSize: '0.75rem', color: 'var(--primary)', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                {selectedIds.length === documents.length ? 'Deselect all' : 'Select all'}
              </button>
            )}
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '10px' }}>
            Leave empty to audit every document you're authorized to see.
          </p>

          {loadingDocs ? (
            <div style={{ padding: '30px', textAlign: 'center' }}>
              <Spinner size={24} />
            </div>
          ) : documents.length === 0 ? (
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>No documents available.</p>
          ) : (
            <div style={{ maxHeight: '260px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '4px', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '6px' }}>
              {documents.map((doc) => {
                const checked = selectedIds.includes(doc.id);
                return (
                  <div
                    key={doc.id}
                    onClick={() => toggleDoc(doc.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '8px 10px',
                      borderRadius: 'var(--radius-sm)',
                      cursor: 'pointer',
                      backgroundColor: checked ? 'var(--primary-subtle)' : 'transparent'
                    }}
                  >
                    {checked ? (
                      <CheckSquare size={16} style={{ color: 'var(--primary)', flexShrink: 0 }} />
                    ) : (
                      <Square size={16} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                    )}
                    <FileText size={14} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                    <span style={{ fontSize: '0.8125rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {doc.original_filename}
                    </span>
                    <Badge variant={doc.status === 'indexed' ? 'success' : 'warning'} className="ml-auto">
                      {doc.status}
                    </Badge>
                  </div>
                );
              })}
            </div>
          )}
          {selectedIds.length > 0 && (
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '8px' }}>
              {selectedIds.length} document{selectedIds.length !== 1 ? 's' : ''} selected
            </p>
          )}
        </div>
      </div>
    </Modal>
  );
};

export default AuditPage;