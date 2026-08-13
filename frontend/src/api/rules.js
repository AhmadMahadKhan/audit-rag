import client from './client';

export const listRules = async () => {
  const res = await client.get('/rules');
  return res.data;
};

export const seedRules = async () => {
  const res = await client.post('/rules/seed');
  return res.data;
};

export const setRuleActive = async (ruleKey, active) => {
  const res = await client.post(`/rules/${ruleKey}/${active ? 'enable' : 'disable'}`);
  return res.data;
};

export const updateRuleConfig = async (ruleKey, config) => {
  const res = await client.put(`/rules/${ruleKey}/config`, { config });
  return res.data;
};

export const executeRulesForDocument = async (documentId) => {
  const res = await client.post(`/rules/${documentId}/execute`);
  return res.data;
};

export const getFindings = async (documentId) => {
  const res = await client.get(`/rules/${documentId}/findings`);
  return res.data;
};
