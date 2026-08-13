import client from './client';

export const getDocumentBundle = async (documentId) => {
  const res = await client.get(`/viewer/${documentId}/bundle`);
  return res.data;
};

export const getOriginalFileUrl = (documentId) => {
  return `/api/v1/viewer/${documentId}/original`;
};

export const searchWithinDocument = async (documentId, query) => {
  const res = await client.get(`/viewer/${documentId}/search?q=${encodeURIComponent(query)}`);
  return res.data;
};
