import React, { useState, useEffect } from 'react';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import StatCard from '../components/dashboard/StatCard';
import Modal from '../components/common/Modal';
import Spinner from '../components/common/Spinner';
import Toast from '../components/common/Toast';
import { createDataset, runEvaluation, listEvalRuns, listDatasets, setQualityGate } from '../api/evaluation';
import { CheckSquare, Play, Plus, Target, Award, ShieldAlert, FileCode, AlertCircle } from 'lucide-react';

export const EvaluationPage = () => {
  const [lastRun, setLastRun] = useState(null);
  const [datasets, setDatasets] = useState([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [runningEval, setRunningEval] = useState(false);
  const [isDatasetModalOpen, setIsDatasetModalOpen] = useState(false);
  const [datasetName, setDatasetName] = useState('');
  const [datasetDesc, setDatasetDesc] = useState('');
  const [toasts, setToasts] = useState([]);
  const [error, setError] = useState(null);

  const addToast = (message, type = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  };

  // Derive gate status from actual run data
  const m = lastRun?.metrics || {};
  const gateStatus = lastRun
    ? (m.faithfulness_score >= 0.90 && m.mean_reciprocal_rank >= 0.85)
      ? 'passed'
      : 'failed'
    : null;

  useEffect(() => {
    // Load datasets and latest eval run
    Promise.all([
      listDatasets().catch(() => []),
      listEvalRuns().catch(() => []),
    ]).then(([ds, runs]) => {
      setDatasets(ds);
      if (ds.length > 0) setSelectedDatasetId(ds[0].id);
      if (runs.length > 0) setLastRun(runs[0]);
      setLoading(false);
    }).catch((err) => {
      setError('Failed to load evaluation data.');
      setLoading(false);
    });
  }, []);

  const handleRunEval = async () => {
    if (!selectedDatasetId) {
      addToast('Please create a dataset first before running evaluation.', 'warning');
      return;
    }
    setRunningEval(true);
    try {
      const res = await runEvaluation(selectedDatasetId);
      setLastRun(res);
      addToast('RAG evaluation benchmark run completed!', 'success');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Evaluation run failed.', 'error');
    } finally {
      setRunningEval(false);
    }
  };

  const handleCreateDataset = async (e) => {
    e.preventDefault();
    if (!datasetName.trim()) return;
    try {
      const newDs = await createDataset(datasetName, datasetDesc);
      setDatasets((prev) => [...prev, newDs]);
      setSelectedDatasetId(newDs.id);
      addToast(`Dataset "${datasetName}" created!`, 'success');
      setIsDatasetModalOpen(false);
      setDatasetName('');
      setDatasetDesc('');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to create dataset.', 'error');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem' }}>RAG System Evaluation & Quality Gates</h2>
          <p style={{ fontSize: '0.875rem' }}>Benchmark retrieval relevance, answer faithfulness, and hallucination safety</p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {datasets.length > 1 && (
            <select
              className="form-select"
              value={selectedDatasetId || ''}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              style={{ width: 'auto' }}
            >
              {datasets.map((ds) => (
                <option key={ds.id} value={ds.id}>{ds.name}</option>
              ))}
            </select>
          )}
          <button className="btn btn-secondary" onClick={() => setIsDatasetModalOpen(true)}>
            <Plus size={16} />
            <span>Create Dataset</span>
          </button>
          <button className="btn btn-primary" onClick={handleRunEval} disabled={runningEval || !selectedDatasetId}>
            {runningEval ? <Spinner size={16} /> : <Play size={16} />}
            <span>Run Benchmark Suite</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ padding: '60px', textAlign: 'center' }}>
          <Spinner size={32} />
        </div>
      ) : error ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--accent-rose)' }}>
          <AlertCircle size={32} style={{ margin: '0 auto 12px' }} />
          <p>{error}</p>
        </div>
      ) : !lastRun ? (
        <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <Target size={36} style={{ margin: '0 auto 12px', color: 'var(--primary)' }} />
          <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>No Evaluation Runs Yet</p>
          <p style={{ fontSize: '0.8125rem', marginTop: '4px' }}>
            Create a benchmark dataset and run an evaluation to see quality metrics.
          </p>
        </div>
      ) : (
        <>
          {/* Quality Scores Grid */}
          <div className="grid-4">
            <StatCard
              label="Overall Retrieval Accuracy"
              value={`${(m.overall_accuracy ?? 0).toFixed(1)}%`}
              icon={Target}
            />
            <StatCard
              label="Mean Reciprocal Rank (MRR)"
              value={(m.mean_reciprocal_rank ?? 0).toFixed(3)}
              icon={Award}
            />
            <StatCard
              label="Faithfulness Score"
              value={`${((m.faithfulness_score ?? 0) * 100).toFixed(1)}%`}
              icon={CheckSquare}
            />
            <StatCard
              label="Answer Relevance Score"
              value={`${((m.answer_relevance_score ?? 0) * 100).toFixed(1)}%`}
              icon={CheckSquare}
            />
          </div>

          {/* Detailed Run Breakdown */}
          <div className="grid-2">
            <Card title="Benchmark Test Execution" subtitle="Latest evaluation batch metrics">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)' }}>
                  <span>Total Ground Truth Test Cases:</span>
                  <strong style={{ fontFamily: 'var(--font-mono)' }}>{lastRun.total_cases}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)' }}>
                  <span>Passed Cases (Faithful & Relevant):</span>
                  <strong style={{ color: 'var(--accent-emerald)', fontFamily: 'var(--font-mono)' }}>{lastRun.passed_cases}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)' }}>
                  <span>Failed / Regression Cases:</span>
                  <strong style={{ color: 'var(--accent-rose)', fontFamily: 'var(--font-mono)' }}>{lastRun.failed_cases}</strong>
                </div>
              </div>
            </Card>

            <Card title="CI/CD Quality Gate Status" subtitle="Threshold criteria for deployment release">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '12px' }}>
                <div style={{ padding: '16px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ fontWeight: 600 }}>Production Deployment Gate</span>
                    <Badge variant={gateStatus === 'passed' ? 'success' : 'danger'}>
                      {gateStatus === 'passed' ? 'PASSED' : 'FAILED'}
                    </Badge>
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                    Requires Faithfulness &gt; 0.90 and MRR &gt; 0.85.
                    Current: {(m.faithfulness_score ?? 0).toFixed(2)} faithfulness, {(m.mean_reciprocal_rank ?? 0).toFixed(2)} MRR.
                  </p>
                </div>
              </div>
            </Card>
          </div>
        </>
      )}

      {/* Dataset Modal */}
      <Modal
        isOpen={isDatasetModalOpen}
        onClose={() => setIsDatasetModalOpen(false)}
        title="Create Evaluation Dataset"
      >
        <form onSubmit={handleCreateDataset}>
          <div className="form-group">
            <label className="form-label">Dataset Name</label>
            <input
              type="text"
              className="form-input"
              value={datasetName}
              onChange={(e) => setDatasetName(e.target.value)}
              placeholder="e.g. Q3 Compliance Benchmark Suite"
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Description</label>
            <textarea
              className="form-textarea"
              rows={3}
              value={datasetDesc}
              onChange={(e) => setDatasetDesc(e.target.value)}
              placeholder="Describe the benchmark scope..."
            />
          </div>
          <div className="modal-footer" style={{ paddingRight: 0, paddingBottom: 0 }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsDatasetModalOpen(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary">Create Dataset</button>
          </div>
        </form>
      </Modal>

      <Toast toasts={toasts} onDismiss={(id) => setToasts((prev) => prev.filter((t) => t.id !== id))} />
    </div>
  );
};

export default EvaluationPage;
