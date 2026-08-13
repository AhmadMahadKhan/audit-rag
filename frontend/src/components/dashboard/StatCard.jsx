import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import Card from '../common/Card';

export const StatCard = ({ label, value, unit, trend_pct, status = 'ok', icon: Icon }) => {
  const isPositive = trend_pct && trend_pct >= 0;
  const statusColor = status === 'warning' ? 'var(--accent-amber)' : status === 'critical' ? 'var(--accent-rose)' : 'var(--accent-emerald)';

  return (
    <Card>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--text-secondary)' }}>{label}</span>
        {Icon && (
          <div style={{ padding: '8px', borderRadius: '8px', backgroundColor: 'var(--bg-surface)', color: 'var(--primary)' }}>
            <Icon size={18} />
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '8px' }}>
        <span style={{ fontSize: '1.75rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
          {typeof value === 'number' ? value.toLocaleString() : value}
        </span>
        {unit && <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>{unit}</span>}
      </div>

      {trend_pct !== undefined && trend_pct !== null && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', fontWeight: 600, color: isPositive ? 'var(--accent-emerald)' : 'var(--accent-amber)' }}>
          {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          <span>{Math.abs(trend_pct)}% from last period</span>
        </div>
      )}
    </Card>
  );
};

export default StatCard;
