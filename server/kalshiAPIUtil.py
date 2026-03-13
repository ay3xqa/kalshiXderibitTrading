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
                mkt["no_price"] = int(float(market["no_ask_dollars"]) * 100)
                mkt["no_prob"] = SMA.integrate_pdf(mkt["target_price"])
                mkt["yes_price"] = int(float(market["yes_ask_dollars"]) * 100)
                mkt["yes_prob"] = 100-mkt["no_prob"]
                market_data.append(mkt)
        sorted_market_data = sorted(market_data, key=lambda x: x['target_price'])
        data["market_data"] = sorted_market_data
        return data
    else:
        print("Error: ", response.status_code, response.text)
        return {}

def get_kalshi_max_day_json(currency, SMA):
    # today = datetime.datetime.now()
    
    # # Extract components for the format
    # year_last_two = today.strftime('%y')
    # month_abbr = today.strftime('%b').upper()
    # day = today.strftime('%d')
    
    # formatted_date = f"{year_last_two}{month_abbr}{day}"

    # print(f"KX{currency}D-{formatted_date}17")
    # market_params = {'event_ticker':f"KX{currency}D-{formatted_date}17"}
    
    now = datetime.datetime.now()
    if now.hour >= 18:  
        event_date = now + datetime.timedelta(days=1) 
    else:
        event_date = now 
    year_last_two = event_date.strftime('%y')
    month_abbr = event_date.strftime('%b').upper()
    day = event_date.strftime('%d')
    formatted_date = f"{year_last_two}{month_abbr}{day}"
    event_ticker = f"KX{currency}D-{formatted_date}18"
    print(event_ticker)
    market_params = {'event_ticker': event_ticker}

    headers = retrieve_auth_header(path=path, method_type=method)
    response = requests.get(base_url+path, headers=headers, params=market_params)
    valid_currency = {"BTC", "ETH"}
    if currency not in valid_currency:
        print("Not valid currency type. Request not made")
        return {}
    if response.status_code == 200:
        markets_response = response.json()
        print(markets_response)
        data = {}
        if markets_response['markets'][0]:
            data["market_title"] = markets_response['markets'][0]["title"]
            market_data = []
            
        # Track opportunities for email alert
        opportunities = []

        #for logging
        rowsAppended = 0
        
        for market in markets_response['markets']:
            if int(float(market["yes_ask_dollars"]) * 100) > 90 or int(float(market["no_ask_dollars"]) * 100) > 90:
                continue
            if market["status"] == "active":
                mkt = {}
                mkt["event_ticker"] = market["ticker"]
                mkt["target_price"] = int(market["floor_strike"]+0.01)
                mkt["no_price"] = int(float(market["no_ask_dollars"]) * 100)
                mkt["no_prob"] = SMA.integrate_pdf(mkt["target_price"])
                mkt["yes_price"] = int(float(market["yes_ask_dollars"]) * 100)
                mkt["yes_prob"] = 100-mkt["no_prob"]


                # entry condition:
                # model_probability > kalshi_price + 10 AND kalshi_price > 50 AND kalshi_price < 90
                price_diff_threshold = 10
                floor_price = 50

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

                if aws_email_config.ENABLE_S3_OPS:
                    if currency == "BTC":
                        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        update_local_csv(timestamp, "BTC", "Daily", "No", mkt["target_price"], mkt["no_prob"], mkt["no_price"])
                        update_local_csv(timestamp, "BTC", "Daily", "Yes", mkt["target_price"], mkt["yes_prob"], mkt["yes_price"])
                        rowsAppended += 1

                market_data.append(mkt)

        print(f"{rowsAppended} rows appended at time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        sorted_market_data = sorted(market_data, key=lambda x: x['target_price'])
        data["market_data"] = sorted_market_data
        return data
    else:
        print("Error: ", response.status_code, response.text)
        return {}
