import pandas as pd
import requests
import os
import re
from datetime import datetime
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import base64

# === Auth Functions (from kalshiAuth.py) ===

def load_private_key(file_path):
    """Load RSA private key from PEM file."""
    with open(file_path, "rb") as key_file:
        return serialization.load_pem_private_key(
            key_file.read(),
            password=None
        )

def sign_request(private_key, timestamp, method, path):
    """Sign request with RSA-PSS."""
    message = f"{timestamp}{method}{path}".encode("utf-8")
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode("utf-8")

# === Configuration ===
# UPDATE THESE PATHS BEFORE RUNNING
KEY_FILE_PATH = "../server/kalshi_key.key"  # <-- UPDATE THIS
KALSHI_ACCESS_KEY = "TODO"      # <-- UPDATE THIS

def get_auth_headers(path, method="GET"):
    """Generate Kalshi API auth headers."""
    private_key = load_private_key(KEY_FILE_PATH)
    timestamp = str(int(datetime.now().timestamp() * 1000))
    signature = sign_request(private_key, timestamp, method, path)

    return {
        "KALSHI-ACCESS-KEY": KALSHI_ACCESS_KEY,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "KALSHI-ACCESS-TIMESTAMP": timestamp
    }

# === Settlement Fetching ===

def date_to_event_ticker(settlement_date):
    """Convert settlement date to Kalshi event ticker.

    Args:
        settlement_date: str like '2025-02-15'

    Returns:
        str like 'KXBTCD-25FEB1517'
    """
    dt = datetime.strptime(settlement_date, '%Y-%m-%d')
    year_2digit = dt.strftime('%y')  # '25'
    month_3char = dt.strftime('%b').upper()  # 'FEB'
    day_2digit = dt.strftime('%d')  # '15'

    return f"KXBTCD-{year_2digit}{month_3char}{day_2digit}17"

def fetch_markets_for_event(event_ticker):
    """Fetch all markets for a given event ticker."""
    base_url = "https://api.elections.kalshi.com"
    path = f"/trade-api/v2/historical/markets/?event_ticker={event_ticker}"

    headers = get_auth_headers(path, "GET")
    response = requests.get(f"{base_url}{path}", headers=headers)

    if response.status_code != 200:
        print(f"Error {response.status_code} for {event_ticker}: {response.text}")
        return None

    return response.json()

def floor_strike_to_strike_price(floor_strike):
    """Convert Kalshi floor_strike to the strike price used in historical CSV.

    Kalshi uses floor_strike like 86499.99 meaning "YES if price > 86499.99"
    which is effectively "YES if price >= 86500".

    Historical CSV uses 86500 as the strike price.

    Args:
        floor_strike: float like 86499.99

    Returns:
        int: strike price like 86500
    """
    return int(floor_strike + 0.01)

def find_highest_yes_strike(markets_response):
    """Find the highest strike price where result was 'yes'.

    Args:
        markets_response: API response containing 'markets' list

    Returns:
        int: highest strike price that settled YES, or None if not found
    """
    markets = markets_response.get('markets', [])

    if not markets:
        return None

    # Filter to YES results and find max floor_strike
    yes_markets = [m for m in markets if m.get('result') == 'yes']

    if not yes_markets:
        return None

    # Get the highest floor_strike among YES results
    highest = max(yes_markets, key=lambda m: m.get('floor_strike', 0))
    floor_strike = highest.get('floor_strike')

    # Convert floor_strike (86499.99) to strike price (86500)
    return floor_strike_to_strike_price(floor_strike)

def fetch_settlement_for_date(settlement_date):
    """Fetch the highest YES strike for a settlement date.

    Args:
        settlement_date: str like '2025-02-15'

    Returns:
        float: highest_yes_strike or None if failed
    """
    event_ticker = date_to_event_ticker(settlement_date)
    print(f"  Fetching {event_ticker} for {settlement_date}...")

    response = fetch_markets_for_event(event_ticker)
    if response is None:
        return None

    return find_highest_yes_strike(response)

# === Main Script ===

def get_unique_settlement_dates(historical_csv_path):
    """Extract unique settlement dates from historical data."""
    df = pd.read_csv(historical_csv_path)
    df['time'] = pd.to_datetime(df['time'])

    # Apply same settlement date logic as backtest
    def get_settlement_date(timestamp):
        if timestamp.hour >= 17:
            return (timestamp + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            return timestamp.strftime('%Y-%m-%d')

    df['settlement_date'] = df['time'].apply(get_settlement_date)
    return sorted(df['settlement_date'].unique())

def main():
    import time

    # Get unique dates from historical data
    historical_path = 'kalshi-historical.csv'
    print(f"Reading dates from {historical_path}...")
    dates = get_unique_settlement_dates(historical_path)
    print(f"Found {len(dates)} unique settlement dates")

    # Fetch settlements
    settlements = []
    for date in dates:
        highest_yes = fetch_settlement_for_date(date)
        if highest_yes is not None:
            settlements.append({
                'settlement_date': date,
                'highest_yes_strike': highest_yes
            })
            print(f"    -> {highest_yes}")
        else:
            print(f"    -> FAILED or no data")

        # Rate limiting - be nice to the API
        time.sleep(1.5)

    # Save to CSV
    output_path = 'settlements.csv'
    df = pd.DataFrame(settlements)
    df.to_csv(output_path, index=False)
    print(f"\nSaved {len(settlements)} settlements to {output_path}")

if __name__ == "__main__":
    main()
