import React, { createContext, useContext, useState, useEffect } from 'react';
import { loginApi, logoutApi } from '../api/auth';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('audit_rag_user');
      if (!saved || saved === 'undefined' || saved === 'null') return null;
      return JSON.parse(saved);
    } catch (e) {
      localStorage.removeItem('audit_rag_user');
      return null;
    }
  });

  const [token, setToken] = useState(() => {
    const savedToken = localStorage.getItem('audit_rag_token');
    if (!savedToken || savedToken === 'undefined' || savedToken === 'null') return null;
    return savedToken;
  });

  const logout = () => {
    const rt = localStorage.getItem('audit_rag_refresh');
    if (rt && rt !== 'undefined') {
      logoutApi(rt);
    }
    setToken(null);
    setUser(null);
    localStorage.removeItem('audit_rag_token');
    localStorage.removeItem('audit_rag_user');
    localStorage.removeItem('audit_rag_refresh');
  };

  useEffect(() => {
    const handleUnauthorized = () => {
      logout();
    };
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, []);

  const login = async (email, password) => {
    const res = await loginApi(email, password);
    const userObj = res.user || { email };
    setToken(res.access_token);
    setUser(userObj);
    localStorage.setItem('audit_rag_token', res.access_token);
    localStorage.setItem('audit_rag_user', JSON.stringify(userObj));
    if (res.refresh_token) {
      localStorage.setItem('audit_rag_refresh', res.refresh_token);
    }
    return res;
  };

  const hasPermission = (permission) => {
    if (!user) return false;
    if (!user.permissions) return true; // admin fallback
    return user.permissions.includes(permission);
  };

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!token, login, logout, hasPermission }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
