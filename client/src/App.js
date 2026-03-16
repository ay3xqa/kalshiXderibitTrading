import React, { useState, useCallback } from 'react';
import AppShell from './components/AppShell';
import Dashboard from './components/Dashboard';
import Calculator from './components/Calculator';
import Placeholder from './components/Placeholder';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [lastUpdate, setLastUpdate] = useState(null);
  const [isConnected, setIsConnected] = useState(true);

  const handleDataUpdate = useCallback((timestamp) => {
    setLastUpdate(timestamp);
    setIsConnected(true);
  }, []);

  const handleConnectionError = useCallback(() => {
    setIsConnected(false);
  }, []);

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <Dashboard
            onDataUpdate={handleDataUpdate}
            onError={handleConnectionError}
          />
        );
      case 'markets':
        return (
          <Dashboard
            onDataUpdate={handleDataUpdate}
            onError={handleConnectionError}
          />
        );
      case 'calculator':
        return <Calculator />;
      case 'portfolio':
        return <Placeholder title="Portfolio" subtitle="Track your positions and P&L across all markets." />;
      case 'trades':
        return <Placeholder title="Trade History" subtitle="View your complete trading history and analytics." />;
      case 'balance':
        return <Placeholder title="Balance" subtitle="Manage your account balance and deposits." />;
      case 'settings':
        return <Placeholder title="Settings" subtitle="Configure your trading preferences and alerts." />;
      default:
        return <Dashboard onDataUpdate={handleDataUpdate} onError={handleConnectionError} />;
    }
  };

  return (
    <AppShell
      activeTab={activeTab}
      onTabChange={setActiveTab}
      lastUpdate={lastUpdate}
      isConnected={isConnected}
    >
      {renderContent()}
    </AppShell>
  );
}

export default App;
