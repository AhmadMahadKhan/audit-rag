import client from './client';

export const performSearch = async (query, mode = 'hybrid', filters = {}, top_k = 20) => {
  const res = await client.post('/search', { query, mode, filters, top_k });
  return res.data;
};

export const getSearchSuggestions = async (q) => {
  const res = await client.get(`/search/suggestions?q=${encodeURIComponent(q)}`);
  return res.data;
};

export const getSearchHistory = async () => {
  const res = await client.get('/search/history');
  return res.data;
};

export const saveSearchQuery = async (name, query, filters = {}, search_mode = 'hybrid') => {
  const res = await client.post('/search/saved', { name, query, filters, search_mode });
  return res.data;
};

export const listSavedSearches = async () => {
  const res = await client.get('/search/saved');
  return res.data;
};

export const runSavedSearch = async (searchId) => {
  const res = await client.post(`/search/saved/${searchId}/run`);
  return res.data;
};

export const deleteSavedSearch = async (searchId) => {
  const res = await client.delete(`/search/saved/${searchId}`);
  return res.data;
};
