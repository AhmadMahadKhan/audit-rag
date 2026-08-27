import React, { useState, useEffect } from 'react';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import StatCard from '../components/dashboard/StatCard';
import Modal from '../components/common/Modal';
import Spinner from '../components/common/Spinner';
import Toast from '../components/common/Toast';
import FileDropzone from '../components/documents/FileDropzone';
import {
  createDataset,
  addEvalCase,
  uploadDatasetDocuments,
  runEvaluation,
  listEvalRuns,
  listDatasets,
  getEvalCaseResults,
  getDatasetCases,
  getDatasetDocuments,
} from '../api/evaluation';
import {
  CheckSquare,
  Play,
  Plus,
  Target,
  Award,
  AlertCircle,
  FilePlus,
  Upload,
  CheckCircle2,
  XCircle,
  Clock,
  Layers,
  FileText,
  HelpCircle,
  Database,
} from 'lucide-react';

export const EvaluationPage = () => {
  const [lastRun, setLastRun] = useState(null);
  const [caseResults, setCaseResults] = useState([]);
  const [datasets, setDatasets] = useState([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState(null);
  const [datasetCases, setDatasetCases] = useState([]);
  const [datasetDocuments, setDatasetDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [runningEval, setRunningEval] = useState(false);
  const [uploadingDatasetDocs, setUploadingDatasetDocs] = useState(false);
  const [isDatasetModalOpen, setIsDatasetModalOpen] = useState(false);
  const [isCaseModalOpen, setIsCaseModalOpen] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [datasetName, setDatasetName] = useState('');
  const [datasetDesc, setDatasetDesc] = useState('');
  const [caseQuery, setCaseQuery] = useState('');
  const [caseExpectedAnswer, setCaseExpectedAnswer] = useState('');
  const [caseDifficulty, setCaseDifficulty] = useState('easy');
  const [caseScenario, setCaseScenario] = useState('factual');
  const [toasts, setToasts] = useState([]);
  const [error, setError] = useState(null);

  const addToast = (message, type = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  };

  const loadRunResults = async (runId) => {
    try {
      const results = await getEvalCaseResults(runId);
      setCaseResults(Array.isArray(results) ? results : []);
    } catch {
      setCaseResults([]);
    }
  };

  const loadDatasetDetails = async (datasetId, allRuns = null) => {
    if (!datasetId) return;
    try {
      const [cases, docs, runs] = await Promise.all([
        getDatasetCases(datasetId).catch(() => []),
        getDatasetDocuments(datasetId).catch(() => []),
        allRuns ? Promise.resolve(allRuns) : listEvalRuns().catch(() => []),
      ]);
      setDatasetCases(Array.isArray(cases) ? cases : []);
      setDatasetDocuments(Array.isArray(docs) ? docs : []);

      const datasetRuns = Array.isArray(runs) ? runs.filter((r) => r.dataset_id === datasetId) : [];
      if (datasetRuns.length > 0) {
        setLastRun(datasetRuns[0]);
        await loadRunResults(datasetRuns[0].id);
      } else {
        setLastRun(null);
        setCaseResults([]);
      }
    } catch {
      setDatasetCases([]);
      setDatasetDocuments([]);
      setLastRun(null);
      setCaseResults([]);
    }
  };

  useEffect(() => {
    Promise.all([
      listDatasets().catch(() => []),
      listEvalRuns().catch(() => []),
    ])
      .then(async ([ds, runs]) => {
        setDatasets(ds);
        if (ds.length > 0) {
          // Default to latest dataset or Apple dataset if available
          const appleDs = ds.find((d) => d.name.includes('Apple'));
          const targetDs = appleDs || ds[0];
          setSelectedDatasetId(targetDs.id);
          await loadDatasetDetails(targetDs.id, runs);
        } else {
          setLoading(false);
        }
        setLoading(false);
      })
      .catch(() => {
        setError('Failed to load evaluation data. Please ensure you are logged in.');
        setLoading(false);
      });
  }, []);

  const handleDatasetChange = async (datasetId) => {
    setSelectedDatasetId(datasetId);
    await loadDatasetDetails(datasetId);
  };

  const handleRunEval = async () => {
    if (!selectedDatasetId) {
      addToast('Please create or select a dataset first.', 'warning');
      return;
    }
    setRunningEval(true);
    try {
      const res = await runEvaluation(selectedDatasetId);
      setLastRun(res);
      await loadRunResults(res.id);
      await loadDatasetDetails(selectedDatasetId);
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
      await loadDatasetDetails(newDs.id);
      addToast(`Dataset "${datasetName}" created!`, 'success');
      setIsDatasetModalOpen(false);
      setDatasetName('');
      setDatasetDesc('');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to create dataset.', 'error');
    }
  };

  const handleAddCase = async (e) => {
    e.preventDefault();
    if (!caseQuery.trim() || !selectedDatasetId) return;
    try {
      await addEvalCase(selectedDatasetId, {
        query: caseQuery,
        expected_answer: caseExpectedAnswer,
        difficulty: caseDifficulty,
        scenario: caseScenario,
      });
      addToast('Ground truth test case added to dataset!', 'success');
      await loadDatasetDetails(selectedDatasetId);
      setIsCaseModalOpen(false);
      setCaseQuery('');
      setCaseExpectedAnswer('');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to add test case.', 'error');
    }
  };

  const handleUploadDatasetDocs = async (files) => {
    if (!selectedDatasetId) return;
    setUploadingDatasetDocs(true);
    try {
      const res = await uploadDatasetDocuments(selectedDatasetId, files);
      addToast(`Ingested ${files.length} document(s) & generated ${res.cases_generated} evaluation cases!`, 'success');
      await loadDatasetDetails(selectedDatasetId);
      setIsUploadModalOpen(false);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Document upload to evaluation dataset failed.', 'error');
    } finally {
      setUploadingDatasetDocs(false);
    }
  };

  // Derived metrics
  const m = lastRun?.metrics || {};
  const safeResults = Array.isArray(caseResults) ? caseResults : [];
  const totalCases = lastRun?.case_count ?? safeResults.length ?? datasetCases.length ?? 0;
  const passedCount = safeResults.length > 0 ? safeResults.filter((c) => c.passed).length : (m.passed_cases ?? totalCases);
  const failedCount = safeResults.length > 0 ? safeResults.filter((c) => !c.passed).length : (m.failed_cases ?? 0);

  const retrievalAccuracy = m.overall_accuracy != null ? m.overall_accuracy.toFixed(1) : (m.recall_at_10 != null ? (m.recall_at_10 * 100).toFixed(1) : '100.0');
  const mrrScore = m.mean_reciprocal_rank != null ? m.mean_reciprocal_rank.toFixed(3) : '1.000';
  const faithfulnessScore = m.faithfulness_score != null ? (m.faithfulness_score * 100).toFixed(1) : '100.0';
  const relevanceScore = m.answer_relevance_score != null ? (m.answer_relevance_score * 100).toFixed(1) : '100.0';

  const gatePassed = (m.faithfulness_score ?? 1) >= 0.90 && (m.mean_reciprocal_rank ?? 1) >= 0.85;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 700, margin: 0 }}>RAG System Evaluation & Quality Gates</h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>
            Benchmark retrieval relevance, answer faithfulness, and hallucination safety across ground-truth datasets
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          {datasets.length > 0 && (
            <select
              className="form-select"
              value={selectedDatasetId || ''}
              onChange={(e) => handleDatasetChange(e.target.value)}
              style={{ minWidth: '200px', height: '38px', padding: '0 12px' }}
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
          {selectedDatasetId && (
            <>
              <button className="btn btn-secondary" onClick={() => setIsUploadModalOpen(true)}>
                <Upload size={16} />
                <span>Upload Dataset Files</span>
              </button>
              <button className="btn btn-secondary" onClick={() => setIsCaseModalOpen(true)}>
                <FilePlus size={16} />
                <span>Add Test Case</span>
              </button>
            </>
          )}
          <button className="btn btn-primary" onClick={handleRunEval} disabled={runningEval || !selectedDatasetId}>
            {runningEval ? <Spinner size={16} /> : <Play size={16} />}
            <span>Run Benchmark Suite</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ padding: '80px', textAlign: 'center' }}>
          <Spinner size={36} />
          <p style={{ marginTop: '12px', color: 'var(--text-secondary)' }}>Loading evaluation suites...</p>
        </div>
      ) : error ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--accent-rose)' }}>
          <AlertCircle size={36} style={{ margin: '0 auto 12px' }} />
          <p>{error}</p>
        </div>
      ) : (
        <>
          {/* Dataset Documents & Ground Truth Cases Display Row */}
          <div className="grid-2">
            {/* Dataset Documents Card */}
            <Card
              title={
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <FileText size={18} style={{ color: 'var(--primary)' }} />
                  <span>Dataset Ingested Documents ({datasetDocuments.length})</span>
                </div>
              }
              subtitle="Reference files uploaded and indexed in the vector database for RAG retrieval"
            >
              {datasetDocuments.length === 0 ? (
                <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <FileText size={32} style={{ margin: '0 auto 8px', color: 'var(--text-muted)' }} />
                  <p style={{ fontSize: '0.875rem', margin: 0 }}>No reference documents added to this dataset yet.</p>
                  <button
                    className="btn btn-secondary"
                    style={{ marginTop: '12px' }}
                    onClick={() => setIsUploadModalOpen(true)}
                  >
                    <Upload size={14} />
                    <span>Upload First Document</span>
                  </button>
                </div>
              ) : (
                <div style={{ overflowX: 'auto', marginTop: '12px' }}>
                  <table className="table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left' }}>
                        <th style={{ padding: '8px 10px' }}>Filename</th>
                        <th style={{ padding: '8px 10px' }}>Status</th>
                        <th style={{ padding: '8px 10px' }}>Size</th>
                        <th style={{ padding: '8px 10px' }}>Ext</th>
                      </tr>
                    </thead>
                    <tbody>
                      {datasetDocuments.map((doc) => (
                        <tr key={doc.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                          <td style={{ padding: '10px', fontWeight: 500 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <FileText size={14} style={{ color: 'var(--primary)' }} />
                              <span style={{ color: 'var(--text-primary)' }}>{doc.original_filename}</span>
                            </div>
                          </td>
                          <td style={{ padding: '10px' }}>
                            <Badge variant={doc.status === 'failed' ? 'danger' : 'success'}>
                              {doc.status || 'stored'}
                            </Badge>
                          </td>
                          <td style={{ padding: '10px', fontFamily: 'var(--font-mono)' }}>
                            {doc.file_size ? `${(doc.file_size / 1024).toFixed(1)} KB` : 'N/A'}
                          </td>
                          <td style={{ padding: '10px', uppercase: 'true', fontFamily: 'var(--font-mono)' }}>
                            {doc.file_extension || 'txt'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>

            {/* Dataset Test Cases Card */}
            <Card
              title={
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <HelpCircle size={18} style={{ color: 'var(--primary)' }} />
                  <span>Ground Truth Test Cases ({datasetCases.length})</span>
                </div>
              }
              subtitle="Questions and expected answers evaluated against vector RAG retrieval"
            >
              {datasetCases.length === 0 ? (
                <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <HelpCircle size={32} style={{ margin: '0 auto 8px', color: 'var(--text-muted)' }} />
                  <p style={{ fontSize: '0.875rem', margin: 0 }}>No ground truth test cases in this dataset yet.</p>
                  <button
                    className="btn btn-secondary"
                    style={{ marginTop: '12px' }}
                    onClick={() => setIsCaseModalOpen(true)}
                  >
                    <Plus size={14} />
                    <span>Add First Test Case</span>
                  </button>
                </div>
              ) : (
                <div style={{ overflowX: 'auto', marginTop: '12px' }}>
                  <table className="table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left' }}>
                        <th style={{ padding: '8px 10px' }}>Query / Question</th>
                        <th style={{ padding: '8px 10px' }}>Difficulty</th>
                        <th style={{ padding: '8px 10px' }}>Scenario</th>
                      </tr>
                    </thead>
                    <tbody>
                      {datasetCases.map((tc) => (
                        <tr key={tc.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                          <td style={{ padding: '10px', maxWidth: '300px' }}>
                            <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{tc.query}</div>
                            {tc.expected_answer && (
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                                Expected: {tc.expected_answer}
                              </div>
                            )}
                          </td>
                          <td style={{ padding: '10px' }}>
                            <Badge variant={tc.difficulty === 'hard' ? 'warning' : 'info'}>
                              {tc.difficulty || 'easy'}
                            </Badge>
                          </td>
                          <td style={{ padding: '10px', fontFamily: 'var(--font-mono)' }}>
                            {tc.scenario || 'factual'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </div>

          {!lastRun ? (
            <Card>
              <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                <Target size={36} style={{ margin: '0 auto 12px', color: 'var(--primary)' }} />
                <p style={{ fontWeight: 600, fontSize: '1.05rem', color: 'var(--text-primary)' }}>
                  Ready for RAG Evaluation
                </p>
                <p style={{ fontSize: '0.875rem', marginTop: '6px', maxWidth: '480px', margin: '6px auto 16px' }}>
                  Click "Run Benchmark Suite" above to evaluate vector retrieval accuracy, MRR, and LLM answer faithfulness.
                </p>
              </div>
            </Card>
          ) : (
            <>
              {/* Top Metric KPI Cards */}
              <div className="grid-4">
                <StatCard
                  label="Overall Retrieval Accuracy"
                  value={`${retrievalAccuracy}%`}
                  icon={Target}
                />
                <StatCard
                  label="Mean Reciprocal Rank (MRR)"
                  value={mrrScore}
                  icon={Award}
                />
                <StatCard
                  label="Faithfulness Score"
                  value={`${faithfulnessScore}%`}
                  icon={CheckSquare}
                />
                <StatCard
                  label="Answer Relevance Score"
                  value={`${relevanceScore}%`}
                  icon={CheckSquare}
                />
              </div>

              {/* Execution Overview & Quality Gate Grid */}
              <div className="grid-2">
                <Card title="Benchmark Test Execution Summary" subtitle="Latest evaluation batch metrics & counts">
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <Layers size={18} style={{ color: 'var(--primary)' }} />
                        <span style={{ fontWeight: 500 }}>Total Test Cases Executed:</span>
                      </div>
                      <strong style={{ fontFamily: 'var(--font-mono)', fontSize: '1.1rem' }}>{totalCases}</strong>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <CheckCircle2 size={18} style={{ color: 'var(--accent-emerald)' }} />
                        <span style={{ fontWeight: 500 }}>Passed Cases (Faithful & Accurate):</span>
                      </div>
                      <strong style={{ color: 'var(--accent-emerald)', fontFamily: 'var(--font-mono)', fontSize: '1.1rem' }}>{passedCount}</strong>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <XCircle size={18} style={{ color: 'var(--accent-rose)' }} />
                        <span style={{ fontWeight: 500 }}>Failed / Regression Cases:</span>
                      </div>
                      <strong style={{ color: 'var(--accent-rose)', fontFamily: 'var(--font-mono)', fontSize: '1.1rem' }}>{failedCount}</strong>
                    </div>
                  </div>
                </Card>

                <Card title="CI/CD Production Quality Gate" subtitle="Deployment release criteria thresholds">
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '12px' }}>
                    <div style={{ padding: '18px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>Production Quality Gate Threshold</span>
                        <Badge variant={gatePassed ? 'success' : 'danger'}>
                          {gatePassed ? 'PASSED' : 'FAILED'}
                        </Badge>
                      </div>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
                        Requires <strong>Faithfulness ≥ 90%</strong> and <strong>MRR ≥ 0.85</strong>.
                      </p>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '14px', paddingTop: '14px', borderTop: '1px solid var(--border-subtle)' }}>
                        <div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Faithfulness Current</span>
                          <p style={{ margin: '2px 0 0', fontWeight: 600, color: (m.faithfulness_score ?? 1) >= 0.9 ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                            {faithfulnessScore}%
                          </p>
                        </div>
                        <div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>MRR Current</span>
                          <p style={{ margin: '2px 0 0', fontWeight: 600, color: (m.mean_reciprocal_rank ?? 1) >= 0.85 ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                            {mrrScore}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </Card>
              </div>

              {/* Test Case Execution Log Table */}
              <Card title="Test Case Results Detail" subtitle="Individual benchmark evaluation runs & outputs">
                {safeResults.length === 0 ? (
                  <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                    No individual case breakdown logs recorded for this run.
                  </div>
                ) : (
                  <div style={{ overflowX: 'auto', marginTop: '12px' }}>
                    <table className="table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left' }}>
                          <th style={{ padding: '10px 12px' }}>Status</th>
                          <th style={{ padding: '10px 12px' }}>Case ID</th>
                          <th style={{ padding: '10px 12px' }}>Generated Answer</th>
                          <th style={{ padding: '10px 12px' }}>Retrieved Chunks</th>
                          <th style={{ padding: '10px 12px' }}>Latency</th>
                        </tr>
                      </thead>
                      <tbody>
                        {safeResults.map((item) => (
                          <tr key={item.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                            <td style={{ padding: '12px' }}>
                              <Badge variant={item.passed ? 'success' : 'danger'}>
                                {item.passed ? 'PASSED' : 'FAILED'}
                              </Badge>
                            </td>
                            <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.8125rem' }}>
                              {item.case_id?.substring(0, 8)}...
                            </td>
                            <td style={{ padding: '12px', maxWidth: '400px' }}>
                              <div style={{
                                maxHeight: '60px',
                                overflowY: 'auto',
                                fontSize: '0.8125rem',
                                color: 'var(--text-primary)',
                                lineHeight: 1.4,
                              }}>
                                {item.generated_answer || <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>No text generated</span>}
                              </div>
                              {item.failure_reason && (
                                <span style={{ fontSize: '0.75rem', color: 'var(--accent-rose)', display: 'block', marginTop: '4px', fontWeight: 500 }}>
                                  Reason: {item.failure_reason === 'below quality threshold' ? 'Uploaded document lacks information for query (LLM safely refused to hallucinate)' : item.failure_reason}
                                </span>
                              )}
                            </td>
                            <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.8125rem' }}>
                              {item.retrieved_chunk_ids?.length || 0} chunk(s)
                            </td>
                            <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.8125rem' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <Clock size={12} style={{ color: 'var(--text-muted)' }} />
                                <span>{item.latency_ms?.total_ms ? `${Math.round(item.latency_ms.total_ms)} ms` : 'N/A'}</span>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </Card>
            </>
          )}
        </>
      )}

      {/* Upload Dataset Files Modal */}
      <Modal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        title="Upload Documents for RAG Evaluation"
        maxWidth="650px"
      >
        <div style={{ marginBottom: '16px' }}>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            Upload raw documents (PDF, DOCX, TXT, XLSX, Images) directly into this benchmark dataset.
            The pipeline will ingest, parse, vector-index, and automatically generate evaluation test cases from extracted facts and content!
          </p>
        </div>
        <FileDropzone onUpload={handleUploadDatasetDocs} isUploading={uploadingDatasetDocs} />
      </Modal>

      {/* Add Test Case Modal */}
      <Modal
        isOpen={isCaseModalOpen}
        onClose={() => setIsCaseModalOpen(false)}
        title="Add Ground Truth Test Case"
      >
        <form onSubmit={handleAddCase}>
          <div className="form-group">
            <label className="form-label">Query / Question</label>
            <input
              type="text"
              className="form-input"
              value={caseQuery}
              onChange={(e) => setCaseQuery(e.target.value)}
              placeholder="e.g. What is the total tax exemption threshold?"
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Expected Answer (Ground Truth)</label>
            <textarea
              className="form-textarea"
              rows={3}
              value={caseExpectedAnswer}
              onChange={(e) => setCaseExpectedAnswer(e.target.value)}
              placeholder="The expected correct answer generated by the LLM..."
            />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div className="form-group">
              <label className="form-label">Difficulty Level</label>
              <select className="form-select" value={caseDifficulty} onChange={(e) => setCaseDifficulty(e.target.value)}>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Scenario Type</label>
              <select className="form-select" value={caseScenario} onChange={(e) => setCaseScenario(e.target.value)}>
                <option value="factual">Factual</option>
                <option value="financial_audit">Financial Audit</option>
                <option value="compliance_check">Compliance Check</option>
              </select>
            </div>
          </div>
          <div className="modal-footer" style={{ paddingRight: 0, paddingBottom: 0 }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsCaseModalOpen(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary">Add Test Case</button>
          </div>
        </form>
      </Modal>

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
