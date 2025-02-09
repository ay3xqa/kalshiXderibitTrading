from kalshiAuth import retrieve_auth_header
from s3_update_util import update_local_csv
import requests
import datetime

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

def get_kalshi_max_day_json(currency, SMA):
    today = datetime.datetime.now()
    
    # Extract components for the format
    year_last_two = today.strftime('%y')
    month_abbr = today.strftime('%b').upper()
    day = today.strftime('%d')
    
    formatted_date = f"{year_last_two}{month_abbr}{day}"

    print(f"KX{currency}D-{formatted_date}17")
    market_params = {'event_ticker':f"KX{currency}D-{formatted_date}17"}
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
            
        # Track opportunities for email alert
        opportunities = []
        
        for market in markets_response['markets']:
            if market["yes_ask"] > 90 or market["no_ask"] > 90:
                continue
            if market["status"] == "active":
                mkt = {}
                mkt["event_ticker"] = market["ticker"]
                mkt["target_price"] = int(market["floor_strike"]+0.01)
                mkt["no_price"] = market["no_ask"]
                mkt["no_prob"] = SMA.integrate_pdf(mkt["target_price"])
                mkt["yes_price"] = market["yes_ask"]
                mkt["yes_prob"] = 100-mkt["no_prob"]


                # entry condition:
                # model_probability > kalshi_price + 10 AND kalshi_price > 50 AND kalshi_price < 90
                price_diff_threshold = 10
                floor_price = 50

                if mkt["no_prob"] > mkt["no_price"] + price_diff_threshold and mkt["no_price"] > floor_price:
                    opportunities.append(
                        f"Price difference detected for {currency} at ${mkt['target_price']}:\n"
                        f"NO Market Price: {mkt['no_price']}% vs Model Probability: {mkt['no_prob']}%"
                    )

                if mkt["yes_prob"] > mkt["yes_price"] + price_diff_threshold and mkt["yes_price"] > floor_price:
                    opportunities.append(
                        f"Price difference detected for {currency} at ${mkt['target_price']}:\n"
                        f"YES Market Price: {mkt['yes_price']}% vs Model Probability: {mkt['yes_prob']}%"
                    )

                if currency == "BTC":
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    update_local_csv(timestamp, "BTC", "Daily", "No", mkt["target_price"], mkt["no_prob"], mkt["no_price"])
                    update_local_csv(timestamp, "BTC", "Daily", "Yes", mkt["target_price"], mkt["yes_prob"], mkt["yes_price"])

                market_data.append(mkt)
                
        # Send email if opportunities are found
        if opportunities:
            from sendGrid import send_email
            html_content = "<h2>Trading OpportunitY Detected:</h2>"
            html_content += "<br>".join([f"<p>{opp}</p>" for opp in opportunities])
            try:
                send_email(html_content)
                print("Alert email sent successfully")
            except Exception as e:
                print(f"Failed to send alert email: {str(e)}")
                
        sorted_market_data = sorted(market_data, key=lambda x: x['target_price'])
        data["market_data"] = sorted_market_data
        return data
    else:
        print("Error: ", response.status_code, response.text)
        return {}

