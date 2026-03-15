import React from 'react';
import { Activity } from 'lucide-react';

export default function Header({ lastUpdate, isConnected = true }) {
  const formatTime = (date) => {
    if (!date) return '--:--:--';
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  return (
    <header className="header">
      <div className="header__logo">
        <div className="header__logo-icon">
          <Activity size={18} color="white" />
        </div>
        <div className="header__logo-text">
          Kalshi<span>X</span>Deribit
        </div>
      </div>

      <div className="header__status">
        <div className="header__status-indicator">
          <div className={`header__status-dot ${!isConnected ? 'header__status-dot--offline' : ''}`} />
          <span>{isConnected ? 'Live' : 'Offline'}</span>
        </div>
        <div className="header__timestamp">
          Last update: {formatTime(lastUpdate)}
        </div>
      </div>
    </header>
  );
}
