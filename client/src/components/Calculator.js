import React, { useState } from 'react';

export default function Calculator() {
  const [contractType, setContractType] = useState('YES');
  const [targetPrice, setTargetPrice] = useState(150000);
  const [lowerBound, setLowerBound] = useState(50000);
  const [upperBound, setUpperBound] = useState(100000);
  const [mode, setMode] = useState('Target');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    let url;
    if (mode === 'Target') {
      url = `http://127.0.0.1:5001/get_probability_target?contract_type=${contractType.toLowerCase()}&target_price=${targetPrice}`;
    } else {
      url = `http://127.0.0.1:5001/get_probability_range?contract_type=${contractType.toLowerCase()}&lower_bound=${lowerBound}&upper_bound=${upperBound}`;
    }

    try {
      const response = await fetch(url, { method: 'GET' });
      if (response.ok) {
        const resultData = await response.json();
        setResult(resultData);
      } else {
        console.error('Error fetching the data.');
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    if (value >= 0 && value <= 300000) {
      setTargetPrice(value);
    }
  };

  return (
    <div className="calculator">
      <div className="calculator__card">
        <h2 className="calculator__title">Probability Calculator</h2>

        <div className="calculator__section">
          <label className="calculator__label">Calculation Mode</label>
          <div className="calculator__toggle-group">
            <button
              className={`calculator__toggle-btn ${mode === 'Target' ? 'calculator__toggle-btn--active' : ''}`}
              onClick={() => {
                setMode('Target');
                setResult(null);
              }}
            >
              Target
            </button>
            <button
              className={`calculator__toggle-btn ${mode === 'Range' ? 'calculator__toggle-btn--active' : ''}`}
              onClick={() => {
                setMode('Range');
                setResult(null);
              }}
            >
              Range
            </button>
          </div>
        </div>

        <div className="calculator__section">
          <label className="calculator__label">Contract Type</label>
          <div className="calculator__toggle-group">
            <button
              className={`calculator__toggle-btn ${contractType === 'YES' ? 'calculator__toggle-btn--active' : ''}`}
              onClick={() => setContractType('YES')}
            >
              YES
            </button>
            <button
              className={`calculator__toggle-btn ${contractType === 'NO' ? 'calculator__toggle-btn--active' : ''}`}
              onClick={() => setContractType('NO')}
            >
              NO
            </button>
          </div>
        </div>

        {mode === 'Target' && (
          <div className="calculator__section">
            <label className="calculator__label">Target Price: ${Number(targetPrice).toLocaleString()}</label>
            <div className="calculator__input-group">
              <input
                type="range"
                className="calculator__slider"
                min="0"
                max="300000"
                value={targetPrice}
                onChange={(e) => setTargetPrice(e.target.value)}
              />
              <input
                type="number"
                className="calculator__input"
                min="0"
                max="300000"
                value={targetPrice}
                onChange={handleInputChange}
                placeholder="Enter target price"
              />
            </div>
          </div>
        )}

        {mode === 'Range' && (
          <div className="calculator__section">
            <label className="calculator__label">Price Range</label>
            <div className="calculator__range-inputs">
              <div className="calculator__input-group">
                <label className="calculator__label" style={{ fontSize: '0.75rem' }}>Lower Bound</label>
                <input
                  type="number"
                  className="calculator__input"
                  min="0"
                  max="300000"
                  value={lowerBound}
                  onChange={(e) => setLowerBound(e.target.value)}
                  placeholder="Lower bound"
                />
              </div>
              <div className="calculator__input-group">
                <label className="calculator__label" style={{ fontSize: '0.75rem' }}>Upper Bound</label>
                <input
                  type="number"
                  className="calculator__input"
                  min="0"
                  max="300000"
                  value={upperBound}
                  onChange={(e) => setUpperBound(e.target.value)}
                  placeholder="Upper bound"
                />
              </div>
            </div>
          </div>
        )}

        <button
          className="calculator__submit-btn"
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? 'Calculating...' : 'Calculate Probability'}
        </button>

        {result && (
          <div className="calculator__result">
            <div className="calculator__result-label">Expected Probability</div>
            <div className="calculator__result-value">{result.data}%</div>
          </div>
        )}
      </div>
    </div>
  );
}
