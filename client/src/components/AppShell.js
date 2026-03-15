import React from 'react';
import Header from './Header';
import Sidebar from './Sidebar';

export default function AppShell({ children, activeTab, onTabChange, lastUpdate, isConnected }) {
  return (
    <div className="app-shell">
      <Header lastUpdate={lastUpdate} isConnected={isConnected} />
      <Sidebar activeTab={activeTab} onTabChange={onTabChange} />
      <main className="app-shell__content">
        {children}
      </main>
    </div>
  );
}
