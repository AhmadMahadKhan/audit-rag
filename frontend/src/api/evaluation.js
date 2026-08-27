import client from './client';

export const createDataset = async (name, description = '') => {
  const res = await client.post(
    `/evaluation/datasets?name=${encodeURIComponent(name)}&description=${encodeURIComponent(description)}`
  );
  return res.data;
};

export const addEvalCase = async (datasetId, caseData) => {
  const res = await client.post(`/evaluation/datasets/${datasetId}/cases`, caseData);
  return res.data;
};

export const getDatasetCases = async (datasetId) => {
  const res = await client.get(`/evaluation/datasets/${datasetId}/cases`);
  return res.data;
};

export const getDatasetDocuments = async (datasetId) => {
  const res = await client.get(`/evaluation/datasets/${datasetId}/documents`);
  return res.data;
};

export const uploadDatasetDocuments = async (datasetId, files) => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });
  const res = await client.post(`/evaluation/datasets/${datasetId}/upload-documents`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const runEvaluation = async (datasetId, configSnapshot = {}, generateAnswers = true) => {
  const res = await client.post(`/evaluation/datasets/${datasetId}/run`, {
    config_snapshot: configSnapshot,
    generate_answers: generateAnswers,
  });
  return res.data;
};

export const getEvalRunDetails = async (runId) => {
  const res = await client.get(`/evaluation/runs/${runId}`);
  return res.data;
};

export const getEvalCaseResults = async (runId) => {
  const res = await client.get(`/evaluation/runs/${runId}/case-results`);
  return res.data;
};

export const listEvalRuns = async () => {
  const res = await client.get('/evaluation/runs');
  return res.data;
};

export const listDatasets = async () => {
  const res = await client.get('/evaluation/datasets');
  return res.data;
};

export const setQualityGate = async (gateData) => {
  const res = await client.post('/evaluation/gates', gateData);
  return res.data;
};
