import React from 'react';
import { Bell, ShieldCheck, Activity, Search } from 'lucide-react';
import Badge from '../common/Badge';

export const Header = ({ title }) => {
  return (
    <header className="top-header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <h1 style={{ fontSize: '1.25rem' }}>{title}</h1>
        <Badge variant="success" icon={ShieldCheck}>
          SOC2 & ISO Compliant
        </Badge>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
          <Activity size={14} style={{ color: 'var(--accent-emerald)' }} />
          <span>Vector Store Active</span>
        </div>

        <div style={{ width: '1px', height: '24px', backgroundColor: 'var(--border-subtle)' }} />

        <button className="btn-icon" title="Notifications" aria-label="Notifications">
          <Bell size={18} />
        </button>
      </div>
    </header>
  );
};

export default Header;
