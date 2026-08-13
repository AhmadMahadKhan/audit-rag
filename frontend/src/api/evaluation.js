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
