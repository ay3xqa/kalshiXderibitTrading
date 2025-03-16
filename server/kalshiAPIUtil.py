import config.aws_email_config as aws_email_config
import datetime
from kalshiAuth import retrieve_auth_header
import requests
from s3_update_util import update_local_csv
from trade_execution import check_and_execute_trade

method = "GET"
base_url = 'https://api.elections.kalshi.com'
path = '/trade-api/v2/markets'

def get_kalshi_max_year_json(currency, SMA):
    market_params = {'series_ticker':"KX"+currency+"MAXY"}
    headers = retrieve_auth_header(path=path, method_type=method)
    response = requests.get(base_url+path, headers=headers, params=market_params)
    valid_currency = {"BTC", "ETH"}
    if currency not in valid_currency:
        print("Not valid currency type. Request not made")
        return {}
    if response.status_code == 200:
        markets_response = response.json()
        data = {}
        if markets_response['markets'][0]:
            data["market_title"] = markets_response['markets'][0]["title"]
            market_data = []
        for market in markets_response['markets']:
            if market["status"] == "active":
                mkt = {}
                last_dash_index = market["ticker"].rfind('-')
                target_price = int(market["floor_strike"]+0.01)
                mkt["event_ticker"] = market["ticker"]
                mkt["target_price"] = int(target_price)
                mkt["no_price"] = market["no_ask"]
                mkt["no_prob"] = SMA.integrate_pdf(mkt["target_price"])
                mkt["yes_price"] = market["yes_ask"]
                mkt["yes_prob"] = 100-mkt["no_prob"]
                market_data.append(mkt)
        sorted_market_data = sorted(market_data, key=lambda x: x['target_price'])
        data["market_data"] = sorted_market_data
        return data
    else:
        print("Error: ", response.status_code, response.text)
        return {}

def _get_formatted_date():
    """Helper function to get the formatted date string for daily markets."""
    today = datetime.datetime.now()
    
    # Extract components for the format
    year_last_two = today.strftime('%y')
    month_abbr = today.strftime('%b').upper()
    day = today.strftime('%d')
    
    return f"{year_last_two}{month_abbr}{day}"

def _fetch_daily_market_data(currency):
    """Fetch raw market data from Kalshi API for daily markets."""
    formatted_date = _get_formatted_date()
    
    print(f"KX{currency}D-{formatted_date}17")
    market_params = {'event_ticker':f"KX{currency}D-{formatted_date}17"}
    headers = retrieve_auth_header(path=path, method_type=method)
    response = requests.get(base_url+path, headers=headers, params=market_params)
    
    valid_currency = {"BTC", "ETH"}
    if currency not in valid_currency:
        print("Not valid currency type. Request not made")
        return None
        
    if response.status_code == 200:
        return response.json() # return the whole response
    else:
        print("Error: ", response.status_code, response.text)
        return None

def _process_market_data(market, currency, SMA):
    """Process a single market's data and return market info dictionary."""
    if market["yes_ask"] > 90 or market["no_ask"] > 90:
        return None
        
    if market["status"] != "active":
        return None
        
    mkt = {}
    mkt["event_ticker"] = market["ticker"]
    mkt["target_price"] = int(market["floor_strike"]+0.01)
    mkt["no_price"] = market["no_ask"]
    mkt["no_prob"] = SMA.integrate_pdf(mkt["target_price"])
    mkt["yes_price"] = market["yes_ask"]
    mkt["yes_prob"] = 100-mkt["no_prob"]
    
    return mkt

def _check_trading_opportunities(mkt, currency):
    """Check if there are trading opportunities and execute trades if found."""
    opportunities = []
    price_diff_threshold = 10
    floor_price = 50

    # Check for NO trade opportunity
    if mkt["no_prob"] > mkt["no_price"] + price_diff_threshold and mkt["no_price"] > floor_price and currency == "BTC":
        opportunities.append(
            f"Price difference detected for {currency} at ${mkt['target_price']}:\n"
            f"NO Market Price: {mkt['no_price']}% vs Model Probability: {mkt['no_prob']}%"
        )
        trade = {'event_ticker': mkt["event_ticker"], 
                'trade_type': 'no', 
                'price': mkt['no_price'], 
                'limit_price': mkt['no_prob'], 
                'difference': mkt["no_prob"]-mkt["no_price"]}
        check_and_execute_trade(trade)

    # Check for YES trade opportunity
    if mkt["yes_prob"] > mkt["yes_price"] + price_diff_threshold and mkt["yes_price"] > floor_price and currency == "BTC":
        opportunities.append(
            f"Price difference detected for {currency} at ${mkt['target_price']}:\n"
            f"YES Market Price: {mkt['yes_price']}% vs Model Probability: {mkt['yes_prob']}%"
        )
        trade = {'event_ticker': mkt["event_ticker"], 
                'trade_type': 'yes', 
                'price': mkt['yes_price'], 
                'limit_price': mkt['yes_prob'], 
                'difference': mkt["yes_prob"]-mkt["yes_price"]}
        check_and_execute_trade(trade)
    
    return opportunities

def _update_csv_data(mkt, currency):
    """Update local CSV data if enabled."""
    rows_appended = 0
    
    if aws_email_config.ENABLE_S3_OPS and currency == "BTC":
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_local_csv(timestamp, "BTC", "Daily", "No", mkt["target_price"], mkt["no_prob"], mkt["no_price"])
        update_local_csv(timestamp, "BTC", "Daily", "Yes", mkt["target_price"], mkt["yes_prob"], mkt["yes_price"])
        rows_appended = 1
        
    return rows_appended

def _send_opportunity_email(opportunities):
    """Send email alert for trading opportunities if enabled."""
    if not aws_email_config.SEND_EMAILS or not opportunities:
        return
        
    from sendGrid import send_email
    html_content = "<h2>Trading Opportunity Detected:</h2>"
    html_content += "<br>".join([f"<p>{opp}</p>" for opp in opportunities])
    
    try:
        send_email(html_content)
        print(f"***Alert email sent successfully at time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ***")
    except Exception as e:
        print(f"Failed to send alert email: {str(e)}")

def get_kalshi_max_day_json(currency, SMA):
    """
    Main function to get Kalshi daily market data, check for trading opportunities,
    update CSV data, and send email alerts if needed.
    """
    # Fetch market data
    markets_response = _fetch_daily_market_data(currency)
    if not markets_response:
        return {}
    
    # Initialize data structures
    data = {}
    market_data = []
    all_opportunities = []
    total_rows_appended = 0
    
    # Set market title if available
    if markets_response['markets'] and len(markets_response['markets']) > 0:
        data["market_title"] = markets_response['markets'][0]["title"]
    
    # Process each market
    for market in markets_response['markets']:
        mkt = _process_market_data(market, currency, SMA)
        if not mkt:
            continue
            
        # Check for trading opportunities
        opportunities = _check_trading_opportunities(mkt, currency)
        all_opportunities.extend(opportunities)
        
        # Update CSV data
        rows_appended = _update_csv_data(mkt, currency)
        total_rows_appended += rows_appended
        
        # Add to market data
        market_data.append(mkt)
    
    # Log CSV updates
    if total_rows_appended > 0:
        print(f"{total_rows_appended} rows appended at time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Send email alerts
    _send_opportunity_email(all_opportunities)
    
    # Sort and return market data
    sorted_market_data = sorted(market_data, key=lambda x: x['target_price'])
    data["market_data"] = sorted_market_data
    return data
