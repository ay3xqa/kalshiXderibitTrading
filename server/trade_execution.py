import uuid
from kalshiAuth import retrieve_auth_header
import requests
from dotenv import load_dotenv
import config.trade_config as trade_config
from sendGrid import send_email
import time

load_dotenv()

global trades_made_today
trades_made_today = 0

# Params documentation: https://trading-api.readme.io/reference/createorder

#Function to actually execute the trade
def execute_trade(action, side, count, order_type, ticker, yes_price=None, no_price=None):
    execute_trade_method = "POST"
    base_url = 'https://api.elections.kalshi.com'
    execute_trade_path = '/trade-api/v2/portfolio/orders'
    execute_trade_headers = retrieve_auth_header(path=execute_trade_path, method_type=execute_trade_method)
    order_id = str(uuid.uuid4())
    payload = {
        "action": action, #buy or sell
        "side": side, #yes or no order
        "count": count, #number of contracts
        "type": order_type, #market or limit (if limit, yes_price or no_price is required)
        "ticker": ticker, #market/event ticker i.e) 
        "client_order_id": order_id, #some unique identifer neccessary
    }
    response = requests.post(base_url+execute_trade_path, headers=execute_trade_headers, json=payload)
    print(response.text)
    print(response.status_code)
    if response.status_code > 299:
        return 0
    return 1

def check_and_execute_trade(trade):
    # Perform portfolio and strategy checks
    print(trade)
    global trades_made_today
    if trades_made_today >= trade_config.DAILY_MAX_TRADES:
        print("Trade Not Executed - Too many trades made today")
        return 
    balance = get_balance()
    if not balance:
        print("Trade Not Executed - Error Getting Balance")
        return 
    if balance < trade_config.MIN_BALANCE_THRESHOLD:
        print("Trade Not Executed - Balance too Low")
        return
    max_allocation = getMaxAllocation(trade)
    if max_allocation > 0:
        if execute_trade(action="buy", side=trade["trade_type"], count=max_allocation, order_type="market", ticker=trade["event_ticker"]):
            trades_made_today+=1
            time.sleep(10)  # Wait for 10 seconds (arbitrary)
            if not create_limit_sell(side=trade["trade_type"], ticker=trade["event_ticker"], limit_price=int(trade["limit_price"])):
                html_content = "<h2>Limit sell failed to execute:</h2>"
                html_content += f"<p>Trade: {trade}</p>"
                send_email(html_content)
def get_positions(ticker):
    method_type = "GET"
    base_url = 'https://api.elections.kalshi.com'
    positions_path = '/trade-api/v2/portfolio/positions'
    positions_headers = retrieve_auth_header(path=positions_path, method_type=method_type)
    params = {
        "ticker": ticker
    }
    response = requests.get(base_url+positions_path, headers=positions_headers, params=params)
    print(response.text)
    if response.status_code > 299:
        return None
    response = response.json()
    return abs(int(response["market_positions"][0]["position"]))-abs(int(response["market_positions"][0]["resting_orders_count"]))

def create_limit_sell(side, ticker, limit_price):
    execute_trade_method = "POST"
    base_url = 'https://api.elections.kalshi.com'
    execute_trade_path = '/trade-api/v2/portfolio/orders'
    execute_trade_headers = retrieve_auth_header(path=execute_trade_path, method_type=execute_trade_method)
    current_ticker_position = get_positions(ticker)
    if not current_ticker_position:
        return 0

    order_id = str(uuid.uuid4())
    payload = {
        "action": "sell", #buy or sell
        "side": side, #yes or no order
        "count": current_ticker_position, #number of contracts
        "type": "limit", #market or limit (if limit, yes_price or no_price is required)
        "ticker": ticker, #market/event ticker i.e) 
        "client_order_id": order_id, #some unique identifer neccessary
    }
    if side == "yes":
        payload["yes_price"] = limit_price
    elif side == "no":
        payload["no_price"] = limit_price

    response = requests.post(base_url+execute_trade_path, headers=execute_trade_headers, json=payload)
    print(response.text)
    print(response.status_code)
    if response.status_code > 299:
        return 0
    return 1

def getMaxAllocation(trade):
    # Dynamic Allocation
    # response = requests.get(base_url+portfolio_path, headers=portfolio_headers)
    # max_allocation = response.json()["balance"]*0.2

    return int(trade_config.TRADE_UNIT_SIZE//trade["price"])

def get_balance():
    try:
        portfolio_method = "GET"
        base_url = 'https://api.elections.kalshi.com'
        portfolio_path = '/trade-api/v2/portfolio/balance'
        portfolio_headers = retrieve_auth_header(path=portfolio_path, method_type=portfolio_method)
        response = requests.get(base_url+portfolio_path, headers=portfolio_headers)
        if response.status_code > 299:
            return None
        balance = response.json()["balance"]
        return balance
    except Exception as e:
        return None
