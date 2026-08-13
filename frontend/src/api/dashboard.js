import client from './client';

export const getDashboardSummary = async () => {
  const res = await client.get('/dashboard/summary');
  return res.data;
};

export const getDashboardActivity = async (limit = 20) => {
  const res = await client.get(`/dashboard/activity?limit=${limit}`);
  return res.data;
};

export const getSystemHealth = async () => {
  const res = await client.get('/dashboard/health');
  return res.data;
};

export const getUploadTrend = async (days = 14) => {
  const res = await client.get(`/dashboard/charts/upload-trend?days=${days}`);
  return res.data;
};

export const getDocumentTypeDistribution = async () => {
  const res = await client.get('/dashboard/charts/document-types');
  return res.data;
};
