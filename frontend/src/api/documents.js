import client from './client';

export const uploadDocuments = async (files) => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });
  const res = await client.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const listDocuments = async (skip = 0, limit = 50) => {
  const res = await client.get(`/documents?skip=${skip}&limit=${limit}`);
  return res.data;
};

export const getDocumentDetails = async (documentId) => {
  const res = await client.get(`/documents/${documentId}`);
  return res.data;
};

export const deleteDocument = async (documentId) => {
  const res = await client.delete(`/documents/${documentId}`);
  return res.data;
};
