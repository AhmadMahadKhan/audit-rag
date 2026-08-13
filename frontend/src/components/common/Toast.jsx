import React from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export const Toast = ({ toasts, onDismiss }) => {
  if (!toasts || toasts.length === 0) return null;

  return (
    <div className="toast-container">
      {toasts.map((toast) => {
        const Icon = toast.type === 'success' ? CheckCircle2 : toast.type === 'error' ? AlertCircle : Info;
        const color = toast.type === 'success' ? 'var(--accent-emerald)' : toast.type === 'error' ? 'var(--accent-rose)' : 'var(--primary)';
        return (
          <div key={toast.id} className="toast">
            <Icon size={18} style={{ color, flexShrink: 0 }} />
            <div style={{ flex: 1 }}>{toast.message}</div>
            <button className="btn-icon" onClick={() => onDismiss(toast.id)} style={{ padding: '2px' }}>
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
};

export default Toast;
