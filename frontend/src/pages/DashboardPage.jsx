import React, { useState, useEffect } from 'react';
import StatCard from '../components/dashboard/StatCard';
import HealthWidget from '../components/dashboard/HealthWidget';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Spinner from '../components/common/Spinner';
import { 
  getDashboardSummary, 
  getDashboardActivity, 
  getSystemHealth, 
  getUploadTrend, 
  getDocumentTypeDistribution 
} from '../api/dashboard';
import { 
  FileText, 
  CheckCircle, 
  Clock, 
  AlertTriangle, 
  HardDrive, 
  Cpu, 
  Users, 
  TrendingUp,
  Activity,
  ArrowUpRight
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const DashboardPage = () => {
  const [summary, setSummary] = useState(null);
  const [activity, setActivity] = useState([]);
  const [health, setHealth] = useState(null);
  const [trends, setTrends] = useState(null);
  const [docTypes, setDocTypes] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([
      getDashboardSummary(),
      getDashboardActivity(10),
      getSystemHealth(),
      getUploadTrend(14),
      getDocumentTypeDistribution()
    ]).then(([sumData, actData, healthData, trendData, typeData]) => {
      setSummary(sumData);
      setActivity(actData);
      setHealth(healthData);
      setTrends(trendData);
      setDocTypes(typeData);
      setLoading(false);
    }).catch((err) => {
      console.error('Error fetching dashboard data:', err);
      setError(err.response?.data?.detail || 'Failed to load dashboard data.');
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '80px', textAlign: 'center' }}>
        <Spinner size={36} />
        <p style={{ marginTop: '16px', fontSize: '0.875rem' }}>Loading Executive Audit Metrics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '80px', textAlign: 'center', color: 'var(--accent-rose)' }}>
        <p style={{ fontWeight: 600 }}>Failed to load dashboard</p>
        <p style={{ fontSize: '0.875rem', marginTop: '8px', color: 'var(--text-muted)' }}>{error}</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Overview Banner */}
      <div style={{
        padding: '24px',
        borderRadius: 'var(--radius-lg)',
        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.15))',
        border: '1px solid rgba(59, 130, 246, 0.2)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', marginBottom: '4px' }}>Audit Ingestion & Compliance Intelligence</h2>
          <p style={{ fontSize: '0.875rem' }}>Live operational status of multi-modal vector search, parsing pipeline, and AI rule evaluation.</p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <Link to="/documents" className="btn btn-primary">
            <span>Upload Documents</span>
            <ArrowUpRight size={16} />
          </Link>
          <Link to="/chat" className="btn btn-secondary">
            <span>Ask AI Assistant</span>
          </Link>
        </div>
      </div>

      {/* KPI Grid */}
      {summary && (
        <div className="grid-4">
          <StatCard 
            label={summary.total_documents?.label} 
            value={summary.total_documents?.value} 
            unit={summary.total_documents?.unit} 
            trend_pct={summary.total_documents?.trend_pct} 
            icon={FileText} 
          />
          <StatCard 
            label={summary.documents_processed?.label} 
            value={summary.documents_processed?.value} 
            unit={summary.documents_processed?.unit} 
            trend_pct={summary.documents_processed?.trend_pct} 
            icon={CheckCircle} 
          />
          <StatCard 
            label={summary.ocr_success_rate?.label} 
            value={summary.ocr_success_rate?.value} 
            unit={summary.ocr_success_rate?.unit} 
            trend_pct={summary.ocr_success_rate?.trend_pct} 
            icon={TrendingUp} 
          />
          <StatCard 
            label={summary.embedding_count?.label} 
            value={summary.embedding_count?.value} 
            unit={summary.embedding_count?.unit} 
            trend_pct={summary.embedding_count?.trend_pct} 
            icon={Cpu} 
          />
        </div>
      )}

      {/* Middle Row: Charts & Distribution */}
      <div className="grid-2">
        <Card title="Ingestion Trend (Last 14 Days)" subtitle="Daily count of processed audit documents">
          <div style={{ height: '220px', marginTop: '16px', display: 'flex', alignItems: 'flex-end', gap: '16px', padding: '10px 0' }}>
            {trends?.points && trends.points.length > 0 ? (
              (() => {
                const maxVal = Math.max(1, ...trends.points.map(p => p.value || 0));
                return trends.points.map((pt, idx) => {
                  const heightPct = Math.round(((pt.value || 0) / maxVal) * 100);
                  return (
                    <div key={idx} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>{pt.value || 0}</span>
                      <div style={{
                        width: '100%',
                        height: `${Math.max(4, heightPct)}%`,
                        backgroundColor: 'var(--primary)',
                        borderRadius: '4px 4px 0 0',
                        transition: 'height 0.3s ease'
                      }} />
                      <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>{pt.label}</span>
                    </div>
                  );
                });
              })()
            ) : (
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>No upload trend data recorded yet.</p>
            )}
          </div>
        </Card>

        <Card title="Document Distribution by Category" subtitle="Breakdown of active knowledge base files">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
            {docTypes?.points && docTypes.points.length > 0 ? (
              (() => {
                const total = docTypes.points.reduce((acc, curr) => acc + (curr.value || 0), 0);
                const colors = ['var(--primary)', 'var(--accent-purple)', 'var(--accent-emerald)', 'var(--accent-amber)', 'var(--accent-rose)'];
                return docTypes.points.map((pt, idx) => {
                  const pct = total > 0 ? Math.round(((pt.value || 0) / total) * 100) : 0;
                  return (
                    <div key={idx}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem', marginBottom: '4px' }}>
                        <span style={{ fontWeight: 500 }}>{pt.label}</span>
                        <span style={{ color: 'var(--text-muted)' }}>{pt.value || 0} docs ({pct}%)</span>
                      </div>
                      <div style={{ height: '8px', width: '100%', backgroundColor: 'var(--bg-surface)', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${pct}%`, backgroundColor: colors[idx % colors.length] }} />
                      </div>
                    </div>
                  );
                });
              })()
            ) : (
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>No document type distribution data yet.</p>
            )}
          </div>
        </Card>
      </div>

      {/* Bottom Row: System Health & Activity Feed */}
      <div className="grid-2">
        <HealthWidget health={health} />

        <Card title="Recent Ingestion & Rule Activity" subtitle="Real-time audit log of platform operations">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '12px' }}>
            {activity.map((act) => (
              <div key={act.id} style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 12px',
                backgroundColor: 'var(--bg-surface)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Activity size={14} style={{ color: 'var(--primary)' }} />
                  <div>
                    <div style={{ fontSize: '0.8125rem', fontWeight: 600 }}>{act.event_type.replace('_', ' ').toUpperCase()}</div>
                    <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>{act.user_email || 'System'} • {act.related_document_id || 'System Task'}</div>
                  </div>
                </div>
                <Badge variant={act.status === 'completed' ? 'success' : 'warning'}>
                  {act.status}
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default DashboardPage;
