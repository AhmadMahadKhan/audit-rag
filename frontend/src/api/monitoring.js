import client from './client';

export const getCostSummary = async (hours = 24) => {
  const res = await client.get(`/monitoring/costs/summary?hours=${hours}`);
  return res.data;
};

export const getCostByUser = async (hours = 24) => {
  const res = await client.get(`/monitoring/costs/by-user?hours=${hours}`);
  return res.data;
};

export const getTopErrors = async () => {
  const res = await client.get('/monitoring/errors/top');
  return res.data;
};

export const getActiveAlerts = async () => {
  const res = await client.get('/monitoring/alerts/active');
  return res.data;
};

export const acknowledgeAlert = async (alertId) => {
  const res = await client.post(`/monitoring/alerts/${alertId}/acknowledge`);
  return res.data;
};
