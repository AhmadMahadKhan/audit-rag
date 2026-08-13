import React, { useState, useEffect } from 'react';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Modal from '../components/common/Modal';
import Spinner from '../components/common/Spinner';
import Toast from '../components/common/Toast';
import { listRules, seedRules, setRuleActive, updateRuleConfig } from '../api/rules';
import { ShieldCheck, Settings, Power, RefreshCw, CheckCircle, AlertTriangle } from 'lucide-react';

export const RulesPage = () => {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRule, setSelectedRule] = useState(null);
  const [configJson, setConfigJson] = useState('');
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [toasts, setToasts] = useState([]);

  const addToast = (message, type = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  };

  const fetchRules = () => {
    setLoading(true);
    listRules()
      .then((data) => {
        setRules(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const handleSeed = async () => {
    try {
      await seedRules();
      addToast('Compliance rules seeded successfully!', 'success');
      fetchRules();
    } catch (err) {
      addToast('Failed to seed rules.', 'error');
    }
  };

  const handleToggle = async (ruleKey, currentActive) => {
    try {
      await setRuleActive(ruleKey, !currentActive);
      addToast(`Rule ${!currentActive ? 'enabled' : 'disabled'}`, 'success');
      fetchRules();
    } catch (err) {
      addToast('Failed to update rule status.', 'error');
    }
  };

  const handleOpenConfig = (rule) => {
    setSelectedRule(rule);
    setConfigJson(JSON.stringify(rule.config, null, 2));
    setIsConfigModalOpen(true);
  };

  const handleSaveConfig = async () => {
    try {
      const parsed = JSON.parse(configJson);
      await updateRuleConfig(selectedRule.rule_key, parsed);
      addToast('Rule configuration updated!', 'success');
      setIsConfigModalOpen(false);
      fetchRules();
    } catch (err) {
      addToast('Invalid JSON configuration syntax.', 'error');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Action Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem' }}>Audit Compliance Rules</h2>
          <p style={{ fontSize: '0.875rem' }}>Configure automated inspection policies applied across ingested documents</p>
        </div>
        <button className="btn btn-secondary" onClick={handleSeed}>
          <RefreshCw size={16} />
          <span>Seed Default Standard Rules</span>
        </button>
      </div>

      {loading ? (
        <div style={{ padding: '60px', textAlign: 'center' }}>
          <Spinner size={32} />
        </div>
      ) : (
        <div className="grid-2">
          {rules.length === 0 ? (
            <div style={{ gridColumn: '1 / -1', padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
              <ShieldCheck size={36} style={{ margin: '0 auto 12px', color: 'var(--primary)' }} />
              <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>No Compliance Rules Configured</p>
              <p style={{ fontSize: '0.8125rem', marginTop: '4px' }}>Click "Seed Default Standard Rules" to load the built-in rule set.</p>
            </div>
          ) : rules.map((rule) => {
            const sevVariant = rule.severity === 'critical' ? 'danger' : rule.severity === 'high' ? 'warning' : 'info';
            return (
              <Card key={rule.id}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <ShieldCheck size={18} style={{ color: rule.is_active ? 'var(--accent-emerald)' : 'var(--text-muted)' }} />
                      <h3 style={{ fontSize: '1rem' }}>{rule.name}</h3>
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      Key: {rule.rule_key} • v{rule.version}
                    </span>
                  </div>
                  <Badge variant={sevVariant}>
                    {rule.severity}
                  </Badge>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '0.8125rem', marginBottom: '16px', color: 'var(--text-secondary)' }}>
                  <span>Category: <strong>{rule.category}</strong></span>
                  <span>Status: <strong style={{ color: rule.is_active ? 'var(--accent-emerald)' : 'var(--text-muted)' }}>{rule.is_active ? 'Active' : 'Disabled'}</strong></span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '8px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
                  <button className="btn btn-secondary" onClick={() => handleOpenConfig(rule)} style={{ fontSize: '0.8125rem', padding: '6px 12px' }}>
                    <Settings size={14} />
                    <span>Configure JSON</span>
                  </button>
                  <button 
                    className={`btn ${rule.is_active ? 'btn-danger' : 'btn-primary'}`} 
                    onClick={() => handleToggle(rule.rule_key, rule.is_active)}
                    style={{ fontSize: '0.8125rem', padding: '6px 12px' }}
                  >
                    <Power size={14} />
                    <span>{rule.is_active ? 'Disable' : 'Enable'}</span>
                  </button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Config Editor Modal */}
      <Modal
        isOpen={isConfigModalOpen}
        onClose={() => setIsConfigModalOpen(false)}
        title={`Configure ${selectedRule?.name}`}
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setIsConfigModalOpen(false)}>Cancel</button>
            <button className="btn btn-primary" onClick={handleSaveConfig}>Save Configuration</button>
          </>
        }
      >
        <div className="form-group">
          <label className="form-label">Rule JSON Configuration Snapshot</label>
          <textarea
            className="form-textarea"
            rows={10}
            style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', lineHeight: 1.5 }}
            value={configJson}
            onChange={(e) => setConfigJson(e.target.value)}
          />
        </div>
      </Modal>

      <Toast toasts={toasts} onDismiss={(id) => setToasts((prev) => prev.filter((t) => t.id !== id))} />
    </div>
  );
};

export default RulesPage;
