import client from './client';

export const listUsers = async () => {
  const res = await client.get('/users');
  return res.data;
};

export const createUser = async ({ email, password, full_name, role_names = [] }) => {
  const res = await client.post('/users', {
    email,
    password,
    full_name,
    role_names,
  });
  return res.data;
};
