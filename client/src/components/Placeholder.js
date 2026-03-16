import React from 'react';
import { Construction } from 'lucide-react';

export default function Placeholder({ title = 'Coming Soon', subtitle }) {
  return (
    <div className="placeholder">
      <div className="placeholder__icon">
        <Construction size={40} />
      </div>
      <h2 className="placeholder__title">{title}</h2>
      <p className="placeholder__subtitle">
        {subtitle || 'This feature is currently under development and will be available soon.'}
      </p>
      <span className="placeholder__badge">In Development</span>
    </div>
  );
}
