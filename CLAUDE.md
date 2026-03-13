# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kalshi X Deribit Trading System - An automated cryptocurrency options trading platform that:
1. Fetches BTC options data from Deribit exchange
2. Uses univariate spline interpolation to calculate risk-neutral probability distributions
3. Compares model probabilities with Kalshi market prices
4. Executes trades when arbitrage opportunities are detected

## Commands

### Backend (Flask Server - port 5001)
```bash
cd server
venv\Scripts\activate                  # Windows
source venv/bin/activate               # Linux/Mac
pip install -r requirements.txt
python app.py
```

### Frontend (React - port 3000)
```bash
cd client
npm install
npm start
```

## Architecture

### Data Flow
```
Deribit API → Strike/Mark Data → UnivariateSplineAnalyzer → PDF (probabilities)
                                                                    ↓
Kalshi API → Market Prices ──────────────────────────────→ Comparison Logic
                                                                    ↓
                                                          Trade Execution → S3 Upload
```

### Key Backend Components

- **app.py**: Flask entry point with APScheduler cron jobs (every 2 min: fetch data & detect opportunities, every 30 min: S3 upload)
- **univariateSplineAnalyzer.py**: Core analytics - fits 3rd-degree spline to options data, derives risk-neutral PDF from 2nd derivative
- **kalshiAPIUtil.py**: Kalshi API integration, opportunity detection (triggers when model_prob > market_price + 10%)
- **deribitAPIUtil.py**: Deribit API integration using ThreadPoolExecutor for parallel requests
- **trade_execution.py**: Order execution, position management, stop loss logic
- **kalshiAuth.py**: RSA PSS signing for Kalshi API authentication

### Key Frontend Components

- **Dashboard.js**: Polls backend every 30 seconds, renders market data
- **Calculator.js**: Interactive probability calculator calling `/get_probability_target` and `/get_probability_range`

### Configuration Files

- **server/config/trade_config.py**: Trading parameters (MIN_BALANCE_THRESHOLD, TRADE_UNIT_SIZE, DAILY_MAX_TRADES)
- **server/config/aws_email_config.py**: Feature flags (ENABLE_S3_OPS, SEND_EMAILS)
- **server/.env**: API keys for Kalshi, AWS, SendGrid

### Data Files

- **server/data/BTC_day_strike_mark_data.json**: Daily expiration options data from Deribit
- **server/data/BTC_year_strike_mark_data.json**: Yearly expiration options data from Deribit

## Important Notes

- Trade cutoff: No trades after 3:30 PM Eastern Time
- Timezone: All market timing uses US/Eastern
- Threading: Deribit API calls use ThreadPoolExecutor
- CORS enabled for frontend-backend communication
- No test framework currently configured
