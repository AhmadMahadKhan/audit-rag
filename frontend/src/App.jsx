import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/layout/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import DocumentsPage from './pages/DocumentsPage';
import SearchPage from './pages/SearchPage';
import ChatPage from './pages/ChatPage';
import RulesPage from './pages/RulesPage';
import EvaluationPage from './pages/EvaluationPage';
import MonitoringPage from './pages/MonitoringPage';
import AuditPage from './pages/AuditPage';
import UsersPage from './pages/UsersPage';


const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

// Gated on the same permission the backend checks (require_permission("users.read")).
const AdminRoute = ({ children }) => {
  const { hasPermission } = useAuth();
  if (!hasPermission('users.read')) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
};

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="documents" element={<DocumentsPage />} />
            <Route path="search" element={<SearchPage />} />
            <Route path="chat" element={<ChatPage />} />
            <Route path="audit" element={<AuditPage />} />

            <Route path="rules" element={<RulesPage />} />
            <Route path="evaluation" element={<EvaluationPage />} />
            <Route path="monitoring" element={<MonitoringPage />} />

            <Route
              path="admin/users"
              element={
                <AdminRoute>
                  <UsersPage />
                </AdminRoute>
              }
            />
          </Route>

          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
