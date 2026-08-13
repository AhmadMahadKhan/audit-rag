import client from './client';

export const loginApi = async (email, password) => {
  const res = await client.post('/auth/login', { email, password });
  return res.data;
};

export const logoutApi = async (refreshToken) => {
  try {
    await client.post('/auth/logout', { refresh_token: refreshToken });
  } catch (err) {
    console.warn('Logout API failed:', err);
  }
};

export const changePasswordApi = async (old_password, new_password) => {
  const res = await client.post('/auth/change-password', { old_password, new_password });
  return res.data;
};
