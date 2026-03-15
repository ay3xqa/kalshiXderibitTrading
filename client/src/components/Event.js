import React from 'react';
import { ArrowUp } from 'lucide-react';

export default function Event({ yes_price, no_price, target_price, yes_prob, no_prob }) {
  const formattedTargetPrice = `$${target_price.toLocaleString()}`;
  const formattedYesPrice = `${yes_price.toFixed(0)}¢`;
  const formattedNoPrice = `${no_price.toFixed(0)}¢`;

  const yesDiff = yes_prob !== null ? yes_prob - yes_price : 0;
  const noDiff = no_prob !== null ? no_prob - no_price : 0;

  const hasYesOpportunity = yesDiff >= 5;
  const hasNoOpportunity = noDiff >= 5;
  const hasOpportunity = hasYesOpportunity || hasNoOpportunity;

  const getSignal = () => {
    if (hasYesOpportunity && yesDiff >= noDiff) {
      return { type: 'buy', label: 'BUY YES' };
    }
    if (hasNoOpportunity) {
      return { type: 'buy', label: 'BUY NO' };
    }
    return null;
  };

  const signal = getSignal();

  return (
    <div className={`event-row ${hasOpportunity ? 'event-row--opportunity' : ''}`}>
      <div className="event-row__target">{formattedTargetPrice}</div>

      <div className="event-row__price-cell">
        <span className="event-row__price">{formattedYesPrice}</span>
        <span className={`event-row__prob ${hasYesOpportunity ? 'event-row__prob--high' : ''}`}>
          {yes_prob !== null ? `Model: ${yes_prob.toFixed(1)}%` : 'Loading...'}
        </span>
      </div>

      <div className="event-row__price-cell">
        <span className="event-row__price">{formattedNoPrice}</span>
        <span className={`event-row__prob ${hasNoOpportunity ? 'event-row__prob--high' : ''}`}>
          {no_prob !== null ? `Model: ${no_prob.toFixed(1)}%` : 'Loading...'}
        </span>
      </div>

      <div className="event-row__signal">
        {signal ? (
          <span className={`event-row__badge event-row__badge--${signal.type}`}>
            <ArrowUp size={12} />
            {signal.label}
          </span>
        ) : (
          <span className="event-row__badge event-row__badge--neutral">—</span>
        )}
      </div>
    </div>
  );
}
