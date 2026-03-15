import React, { useState, useEffect, useRef } from 'react';
import { RefreshCw, TrendingUp, AlertCircle, Clock, BarChart3 } from 'lucide-react';
import axios from 'axios';
import Market from './Market';
import StatCard from './StatCard';

export default function Dashboard({ onDataUpdate, onError }) {
  const [markets, setMarkets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Use refs to avoid dependency issues with callbacks
  const onDataUpdateRef = useRef(onDataUpdate);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onDataUpdateRef.current = onDataUpdate;
    onErrorRef.current = onError;
  }, [onDataUpdate, onError]);

  const fetchKalshiJson = async (isManualRefresh = false) => {
    if (isManualRefresh) {
      setRefreshing(true);
    }

    try {
      const response = await axios.get(
        `http://127.0.0.1:5001/get_all_kalshi_markets_json`
      );
      setMarkets(response.data.data || []);
      onDataUpdateRef.current?.(new Date());
    } catch (error) {
      console.error('Error fetching Kalshi Data:', error);
      onErrorRef.current?.();
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchKalshiJson();

    // Backend updates every 2 minutes due to Kalshi/Deribit rate limits
    const intervalId = setInterval(() => {
      fetchKalshiJson();
    }, 30000);

    return () => clearInterval(intervalId);
  }, []);

  const handleRefresh = () => {
    fetchKalshiJson(true);
  };

  // Calculate stats
  const totalMarkets = markets.length;
  const opportunityCount = markets.reduce((count, market) => {
    return count + (market.market_data || []).filter(event => {
      const yesDiff = event.yes_prob !== null ? event.yes_prob - event.yes_price : 0;
      const noDiff = event.no_prob !== null ? event.no_prob - event.no_price : 0;
      return yesDiff >= 5 || noDiff >= 5;
    }).length;
  }, 0);

  if (loading) {
    return (
      <div className="dashboard">
        <div className="dashboard__loading">
          <div className="dashboard__loading-spinner" />
          <span>Loading market data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard__header">
        <h1 className="dashboard__title">Market Overview</h1>
        <button
          className={`dashboard__refresh-btn ${refreshing ? 'dashboard__refresh-btn--loading' : ''}`}
          onClick={handleRefresh}
          disabled={refreshing}
        >
          <RefreshCw size={16} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <div className="dashboard__stats">
        <StatCard
          label="Active Markets"
          value={totalMarkets}
          icon={BarChart3}
        />
        <StatCard
          label="Opportunities"
          value={opportunityCount}
          icon={TrendingUp}
          variant={opportunityCount > 0 ? 'green' : undefined}
        />
        <StatCard
          label="Refresh Interval"
          value="30s"
          icon={Clock}
        />
      </div>

      <div className="dashboard__markets">
        {markets.length > 0 ? (
          markets.map((market, index) => (
            <Market key={index} kalshiData={market} />
          ))
        ) : (
          <div className="dashboard__empty">
            <AlertCircle className="dashboard__empty-icon" size={48} />
            <span>No market data available</span>
          </div>
        )}
      </div>
    </div>
  );
}
