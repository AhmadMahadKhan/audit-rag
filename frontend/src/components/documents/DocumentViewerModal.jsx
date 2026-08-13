import React, { useState, useEffect } from 'react';
import Modal from '../common/Modal';
import Tabs from '../common/Tabs';
import Badge from '../common/Badge';
import Spinner from '../common/Spinner';
import { getDocumentBundle } from '../../api/viewer';
import { executeRulesForDocument, getFindings } from '../../api/rules';
import { FileText, Shield, Layers, Hash, Database, CheckCircle, AlertTriangle } from 'lucide-react';

export const DocumentViewerModal = ({ documentId, isOpen, onClose }) => {
  const [bundle, setBundle] = useState(null);
  const [findings, setFindings] = useState([]);
  const [activeTab, setActiveTab] = useState('summary');
  const [loading, setLoading] = useState(false);
  const [executingRules, setExecutingRules] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && documentId) {
      setLoading(true);
      setError(null);
      setBundle(null);
      Promise.all([
        getDocumentBundle(documentId),
        getFindings(documentId).catch(() => [])
      ]).then(([bundleData, findingsData]) => {
        setBundle(bundleData);
        setFindings(findingsData);
        setLoading(false);
      }).catch((err) => {
        console.error('Error fetching bundle:', err);
        setError(err.response?.data?.detail || 'Failed to load document bundle.');
        setLoading(false);
      });
    }
  }, [isOpen, documentId]);

  const handleRunRules = async () => {
    setExecutingRules(true);
    try {
      await executeRulesForDocument(documentId);
      const updatedFindings = await getFindings(documentId);
      setFindings(updatedFindings);
    } catch (err) {
      console.error('Failed rule execution:', err);
    } finally {
      setExecutingRules(false);
    }
  };

  if (!isOpen) return null;

  const tabs = [
    { id: 'summary', label: 'Canonical Summary & Meta' },
    { id: 'entities', label: 'Extracted Entities & Facts' },
    { id: 'chunks', label: 'Vector Chunks' },
    { id: 'compliance', label: 'Audit Compliance Findings', badge: findings.length }
  ];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={bundle?.document?.original_filename || `Document ${documentId}`}
      maxWidth="850px"
    >
      {loading ? (
        <div style={{ padding: '60px', textAlign: 'center' }}>
          <Spinner size={32} />
          <p style={{ marginTop: '12px', fontSize: '0.875rem' }}>Loading Deep Inspection Bundle...</p>
        </div>
      ) : error ? (
        <div style={{ padding: '60px', textAlign: 'center', color: 'var(--accent-rose)' }}>
          <AlertTriangle size={32} style={{ margin: '0 auto 12px' }} />
          <p style={{ fontWeight: 600 }}>Failed to load document</p>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '8px' }}>{error}</p>
        </div>
      ) : bundle ? (
        <div>
          {/* Header Info Pill */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 16px',
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 'var(--radius-md)',
            marginBottom: '20px',
            border: '1px solid var(--border-subtle)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <FileText size={20} style={{ color: 'var(--primary)' }} />
              <div>
                <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Classification: </span>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  {bundle.classification?.primary_category || 'Unclassified'}
                </span>
              </div>
            </div>
            <Badge variant="success">
              {bundle.embedding_status?.vector_store || 'Vectorized'}
            </Badge>
          </div>

          <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

          {/* Tab 1: Summary & Meta */}
          {activeTab === 'summary' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ padding: '16px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-md)' }}>
                <h4 style={{ fontSize: '0.875rem', marginBottom: '8px', color: 'var(--primary)' }}>Executive Summary</h4>
                <p style={{ fontSize: '0.875rem', lineHeight: 1.6 }}>{bundle.canonical_summary?.summary}</p>
              </div>

              <div>
                <h4 style={{ fontSize: '0.875rem', marginBottom: '10px' }}>Key Metadata</h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
                  {bundle.metadata?.map((meta, idx) => (
                    <div key={idx} style={{ padding: '10px 12px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>{meta.key}</span>
                      <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>{meta.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Entities & Facts */}
          {activeTab === 'entities' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <h4 style={{ fontSize: '0.875rem', marginBottom: '10px' }}>Named Entities</h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {bundle.entities?.map((ent, idx) => (
                    <span key={idx} style={{ padding: '6px 12px', borderRadius: 'var(--radius-full)', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', fontSize: '0.8125rem' }}>
                      <strong>{ent.name}</strong> <span style={{ color: 'var(--text-muted)' }}>({ent.type})</span>
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <h4 style={{ fontSize: '0.875rem', marginBottom: '10px' }}>Extracted Facts</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {bundle.facts?.map((fact, idx) => (
                    <div key={idx} style={{ padding: '10px 14px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', fontSize: '0.875rem' }}>
                      "{fact.statement}"
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Tab 3: Chunks */}
          {activeTab === 'chunks' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {bundle.chunks?.map((chk, idx) => (
                <div key={idx} style={{ padding: '12px 14px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    <span>Page {chk.page} • Chunk ID: {chk.id}</span>
                    <span>{chk.embedding_dimensions}d vector</span>
                  </div>
                  <p style={{ fontSize: '0.8125rem', fontFamily: 'var(--font-sans)', color: 'var(--text-primary)' }}>{chk.text}</p>
                </div>
              ))}
            </div>
          )}

          {/* Tab 4: Compliance Findings */}
          {activeTab === 'compliance' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h4 style={{ fontSize: '0.9375rem' }}>Audit Rule Evaluation</h4>
                  <p style={{ fontSize: '0.8125rem' }}>Automated rule checks executed against document content</p>
                </div>
                <button className="btn btn-primary" onClick={handleRunRules} disabled={executingRules}>
                  {executingRules ? <Spinner size={14} /> : <Shield size={14} />}
                  <span>Re-evaluate Rules</span>
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {findings.map((f, idx) => (
                  <div key={idx} style={{ padding: '14px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {f.triggered ? <AlertTriangle size={16} style={{ color: 'var(--accent-amber)' }} /> : <CheckCircle size={16} style={{ color: 'var(--accent-emerald)' }} />}
                        <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>{f.rule_name}</span>
                      </div>
                      <Badge variant={f.triggered ? 'warning' : 'success'}>
                        {f.triggered ? 'Rule Flagged' : 'Passed'}
                      </Badge>
                    </div>
                    <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>{f.description}</p>
                    {f.recommendation && (
                      <div style={{ marginTop: '8px', padding: '8px 12px', backgroundColor: 'var(--bg-card)', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem', color: 'var(--primary)' }}>
                        <strong>Recommendation:</strong> {f.recommendation}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : null}
    </Modal>
  );
};

export default DocumentViewerModal;
