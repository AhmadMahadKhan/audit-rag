import React from 'react';
import { Loader2 } from 'lucide-react';

export const Spinner = ({ size = 20, className = '' }) => {
  return <Loader2 size={size} className={`spin ${className}`} style={{ color: 'var(--primary)' }} />;
};

export default Spinner;
