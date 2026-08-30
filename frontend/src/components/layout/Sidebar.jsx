import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileText, 
  Search, 
  MessageSquare, 
  ShieldCheck, 
  CheckSquare, 
  Activity, 
  Shield, 
  LogOut,
  Sparkles,
  Users
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Sidebar = () => {
  const { user, logout, hasPermission } = useAuth();

  const navItems = [
    { label: 'Executive Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Document Hub', path: '/documents', icon: FileText },
    { label: 'Audit Search', path: '/search', icon: Search },
    { label: 'AI Assistant (Chat)', path: '/chat', icon: MessageSquare },
    { label: 'Rule Engine', path: '/rules', icon: ShieldCheck },
    { label: 'Audit', path: '/audit', icon: ShieldCheck },
    { label: 'RAG Evaluation', path: '/evaluation', icon: CheckSquare },
    { label: 'System Monitoring', path: '/monitoring', icon: Activity },
    ...(hasPermission('users.read') ? [{ label: 'User Management', path: '/admin/users', icon: Users }] : []),
  ];

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{ 
          width: '36px', 
          height: '36px', 
          borderRadius: '10px', 
          background: 'linear-gradient(135deg, var(--primary), var(--accent-purple))', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: 'white',
          boxShadow: '0 0 16px rgba(59, 130, 246, 0.4)'
        }}>
          <Shield size={20} />
        </div>
        <div>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, letterSpacing: '-0.03em', lineHeight: 1.1 }}>AUDIT-RAG</h2>
          <span style={{ fontSize: '0.6875rem', color: 'var(--accent-emerald)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>Enterprise AI</span>
        </div>
      </div>

      {/* Nav Menu */}
      <nav style={{ flex: 1, padding: '16px 12px', display: 'flex', flexDirection: 'column', gap: '4px', overflowY: 'auto' }}>
        <div style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', padding: '8px 12px' }}>
          Platform Workspace
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `btn ${isActive ? 'btn-primary' : 'btn-secondary'}`}
              style={({ isActive }) => ({
                justifyContent: 'flex-start',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: isActive ? 'var(--primary)' : 'transparent',
                borderColor: 'transparent',
                color: isActive ? 'white' : 'var(--text-secondary)',
                fontWeight: isActive ? 600 : 500
              })}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* User Footer */}
      <div style={{ padding: '16px', borderTop: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-surface)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
          <div style={{ 
            width: '34px', 
            height: '34px', 
            borderRadius: 'var(--radius-full)', 
            backgroundColor: 'var(--primary-subtle)', 
            color: 'var(--primary)',
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            fontWeight: 700,
            fontSize: '0.875rem'
          }}>
            {user?.full_name ? user.full_name.charAt(0) : 'A'}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
              {user?.full_name || 'Compliance Auditor'}
            </div>
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
              {user?.role || 'Administrator'}
            </div>
          </div>
        </div>
        <button 
          onClick={logout} 
          className="btn btn-secondary" 
          style={{ width: '100%', fontSize: '0.8125rem', padding: '6px 12px', justifyContent: 'center' }}
        >
          <LogOut size={14} />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
