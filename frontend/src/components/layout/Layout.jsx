import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

export const Layout = () => {
  const location = useLocation();

  const titleMap = {
    '/dashboard': 'Executive Dashboard',
    '/documents': 'Document Processing Hub',
    '/search': 'Audit RAG Vector Search',
    '/chat': 'AI Audit Assistant',
    '/rules': 'Compliance Rule Engine',
    '/evaluation': 'RAG Quality Benchmark',
    '/monitoring': 'System Analytics & Cost Monitoring',
    '/audit' :'Audit',
    '/admin/users': 'User Management',
  };

  const currentTitle = titleMap[location.pathname] || 'Audit RAG Platform';

  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-wrapper">
        <Header title={currentTitle} />
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
