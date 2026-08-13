import client from './client';

export const listConversations = async () => {
  const res = await client.get('/chat/conversations');
  return res.data;
};

export const createConversation = async (title = 'New Audit Analysis') => {
  const res = await client.post('/chat/conversations', { title });
  return res.data;
};

export const getConversationMessages = async (conversationId) => {
  const res = await client.get(`/chat/conversations/${conversationId}/messages`);
  return res.data;
};

export const sendMessage = async (conversationId, question, filters = null, provider = null) => {
  const res = await client.post(`/chat/conversations/${conversationId}/messages`, {
    question,
    filters,
    provider,
  });
  return res.data;
};

export const deleteConversation = async (conversationId) => {
  const res = await client.delete(`/chat/conversations/${conversationId}`);
  return res.data;
};
