import React, { useState, useEffect } from 'react';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import StatCard from '../components/dashboard/StatCard';
import Table from '../components/common/Table';
import Spinner from '../components/common/Spinner';
import Toast from '../components/common/Toast';
import { getCostSummary, getCostByUser, getTopErrors, getActiveAlerts, acknowledgeAlert } from '../api/monitoring';
import { DollarSign, Cpu, AlertTriangle, CheckCircle2, ShieldAlert, Activity } from 'lucide-react';

export const MonitoringPage = () => {
  const [costData, setCostData] = useState(null);
  const [userCosts, setUserCosts] = useState([]);
  const [topErrors, setTopErrors] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState([]);

  const addToast = (message, type = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  };

  const fetchMonitoringData = () => {
    setLoading(true);
    Promise.all([
      getCostSummary(24),
      getCostByUser(24),
      getTopErrors(),
      getActiveAlerts()
    ]).then(([costRes, userRes, errorRes, alertRes]) => {
      setCostData(costRes);
      setUserCosts(userRes);
      setTopErrors(errorRes);
      setAlerts(alertRes);
      setLoading(false);
    }).catch((err) => {
      console.error(err);
      setLoading(false);
    });
  };

  useEffect(() => {
    fetchMonitoringData();
  }, []);

  const handleAcknowledge = async (alertId) => {
    try {
      await acknowledgeAlert(alertId);
      addToast('Alert acknowledged successfully', 'success');
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
    } catch (err) {
      addToast('Failed to acknowledge alert', 'error');
    }
  };

  const errorColumns = [
    {
      header: 'Error Category / Type',
      accessor: 'error_type',
      render: (row) => <span style={{ fontWeight: 600, color: 'var(--accent-rose)' }}>{row.error_type}</span>
    },
    {
      header: 'Occurrences',
      accessor: 'count',
      render: (row) => <Badge variant="warning">{row.count} times</Badge>
    },
    {
      header: 'Sample Log Message',
      accessor: 'sample_message',
      render: (row) => <span style={{ fontSize: '0.8125rem', fontFamily: 'var(--font-mono)' }}>{row.sample_message}</span>
    },
    {
      header: 'Last Seen',
      accessor: 'last_seen',
      render: (row) => <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{new Date(row.last_seen).toLocaleTimeString()}</span>
    }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem' }}>System Analytics & LLM Cost Monitoring</h2>
          <p style={{ fontSize: '0.875rem' }}>Real-time telemetry, model spending breakdown, and operational alert center</p>
        </div>
      </div>

      {loading ? (
        <div style={{ padding: '60px', textAlign: 'center' }}>
          <Spinner size={32} />
        </div>
      ) : (
        <>
          {/* KPI Summary Cards */}
          {costData && (
            <div className="grid-3">
              <StatCard 
                label="Total LLM Expenditure (24h)" 
                value={`$${(costData.total_cost_usd ?? 0).toFixed(2)}`} 
                trend_pct={-3.4} 
                icon={DollarSign} 
              />
              <StatCard 
                label="Tokens Processed" 
                value={costData.total_tokens_processed ?? 0} 
                unit="tokens" 
                trend_pct={12.0} 
                icon={Cpu} 
              />
              <StatCard 
                label="Total LLM Model Invocations" 
                value={costData.total_llm_calls ?? 0} 
                unit="calls" 
                trend_pct={5.2} 
                icon={Activity} 
              />
            </div>
          )}

          {/* Active Firing Alerts Banner */}
          {alerts.length > 0 && (
            <Card style={{ borderColor: 'var(--accent-amber)', backgroundColor: 'var(--accent-amber-subtle)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <AlertTriangle size={24} style={{ color: 'var(--accent-amber)' }} />
                  <div>
                    <h3 style={{ fontSize: '1rem', color: 'var(--accent-amber)' }}>Firing Telemetry Alerts ({alerts.length})</h3>
                    <p style={{ fontSize: '0.8125rem', color: 'var(--text-primary)' }}>
                      {alerts[0].name}: current value {alerts[0].current_value} exceeded threshold {alerts[0].threshold}
                    </p>
                  </div>
                </div>
                <button className="btn btn-secondary" onClick={() => handleAcknowledge(alerts[0].id)}>
                  <CheckCircle2 size={16} />
                  <span>Acknowledge</span>
                </button>
              </div>
            </Card>
          )}

          {/* Cost Distribution Breakdown */}
          <div className="grid-2">
            <Card title="Cost by LLM Model" subtitle="Expenditure across embedding & generative engines">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '12px' }}>
                {costData?.cost_by_model?.map((m, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)' }}>
                    <div>
                      <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>{m.model}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{m.calls} invocations</div>
                    </div>
                    <span style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--primary)', fontFamily: 'var(--font-mono)' }}>
                      ${(m.cost ?? 0).toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </Card>

            <Card title="Cost by User Account" subtitle="Top auditor expenditure distribution">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '12px' }}>
                {userCosts.map((u, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)' }}>
                    <div>
                      <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>{u.user_email}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{u.calls} API queries</div>
                    </div>
                    <span style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--accent-emerald)', fontFamily: 'var(--font-mono)' }}>
                      ${(u.cost ?? 0).toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Top Error Log Table */}
          <Card title="Top Backend Error Telemetry" subtitle="Exceptions captured in observability logs">
            <Table columns={errorColumns} data={topErrors} />
          </Card>
        </>
      )}

      <Toast toasts={toasts} onDismiss={(id) => setToasts((prev) => prev.filter((t) => t.id !== id))} />
    </div>
  );
};

export default MonitoringPage;
