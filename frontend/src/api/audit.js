import client from './client';

export const startAudit = async (name, documentIds = null) => {
  const res = await client.post('/audit/runs', { name, document_ids: documentIds });
  return res.data;
};

export const listAuditRuns = async () => {
  const res = await client.get('/audit/runs');
  return res.data;
};

export const getAuditRun = async (runId) => {
  const res = await client.get(`/audit/runs/${runId}`);
  return res.data;
};
export const downloadAuditReportPdf = async (runId, filename = 'audit-report.pdf') => {
  const res = await client.get(`/audit/runs/${runId}/report/pdf`, { responseType: 'blob' });
  const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const getAuditMemoryTrail = async (runId) => {
  const res = await client.get(`/audit/runs/${runId}/memory`);
  return res.data;
};

export const getAuditReport = async (runId) => {
  const res = await client.get(`/audit/runs/${runId}/report`);
  return res.data;
};
