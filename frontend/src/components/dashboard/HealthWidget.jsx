import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { Activity, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';

export const HealthWidget = ({ health }) => {
  if (!health) return null;

  return (
    <Card title="System Architecture & Health" subtitle="Real-time status of backend services and databases">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '12px' }}>
        {health.services?.map((svc, idx) => {
          const isUp = svc.status === 'up';
          return (
            <div 
              key={idx} 
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between',
                padding: '12px 14px',
                backgroundColor: 'var(--bg-surface)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                {isUp ? (
                  <CheckCircle2 size={16} style={{ color: 'var(--accent-emerald)' }} />
                ) : (
                  <AlertTriangle size={16} style={{ color: 'var(--accent-amber)' }} />
                )}
                <span style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-primary)' }}>{svc.name}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                {svc.latency_ms && (
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {svc.latency_ms} ms
                  </span>
                )}
                <Badge variant={isUp ? 'success' : 'warning'}>
                  {svc.status}
                </Badge>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

export default HealthWidget;
