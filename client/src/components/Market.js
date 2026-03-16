import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import Event from './Event';

export default function Market({ kalshiData }) {
  const [isExpanded, setIsExpanded] = useState(true);

  const toggleMarket = () => {
    setIsExpanded(!isExpanded);
  };

  const events = kalshiData.market_data || [];

  return (
    <div className={`market-card ${isExpanded ? 'market-card--expanded' : ''}`}>
      <div className="market-card__header" onClick={toggleMarket}>
        <div className="market-card__info">
          <div className="market-card__icon">BTC</div>
          <span className="market-card__title">{kalshiData.market_title}</span>
        </div>
        <div className="market-card__toggle">
          <ChevronDown size={20} />
        </div>
      </div>

      <div className="market-card__body">
        <div className="market-card__columns">
          <span>Target</span>
          <span>YES</span>
          <span>NO</span>
          <span>Signal</span>
        </div>
        <div className="market-card__events">
          {events.length > 0 ? (
            events.map((event, index) => (
              <Event
                key={index}
                yes_price={event.yes_price}
                no_price={event.no_price}
                target_price={event.target_price}
                yes_prob={event.yes_prob}
                no_prob={event.no_prob}
              />
            ))
          ) : (
            <div className="market-card__empty">
              No events available for this market.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
