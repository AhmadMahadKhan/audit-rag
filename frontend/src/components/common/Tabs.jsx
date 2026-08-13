import React from 'react';

export const Tabs = ({ tabs, activeTab, onChange }) => {
  return (
    <div className="tab-list">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
          {tab.badge !== undefined && (
            <span style={{ 
              marginLeft: '6px', 
              fontSize: '0.75rem', 
              padding: '2px 6px', 
              borderRadius: '99px',
              backgroundColor: activeTab === tab.id ? 'var(--primary-subtle)' : 'var(--bg-surface)',
              color: activeTab === tab.id ? 'var(--primary)' : 'var(--text-muted)'
            }}>
              {tab.badge}
            </span>
          )}
        </button>
      ))}
    </div>
  );
};

export default Tabs;
