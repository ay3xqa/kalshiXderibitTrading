import React from 'react';

export default function StatCard({ label, value, icon: Icon, variant }) {
  const valueClass = variant ? `stat-card__value--${variant}` : '';

  return (
    <div className="stat-card">
      <div className="stat-card__label">
        {Icon && <Icon className="stat-card__icon" size={16} />}
        {label}
      </div>
      <div className={`stat-card__value ${valueClass}`}>
        {value}
      </div>
    </div>
  );
}
