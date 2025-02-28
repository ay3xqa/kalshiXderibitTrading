from flask import Flask, request, jsonify
from deribitAPIUtil import main_get_strike_and_mark_price, get_all_strike_mark_data_threading
from kalshiAPIUtil import get_kalshi_max_year_json, get_kalshi_max_day_json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from univariateSplineAnalyzer import UnivariateSplineAnalyzer
from flask_cors import CORS
from s3_update_util import merge_and_upload_to_s3
from sendGrid import send_email
import os
import json
import time
from threading import Lock

app = Flask(__name__)
CORS(app)

# Global variables for analyzers
btc_day_analyzer = None
btc_year_analyzer = None 

def initialize_data():
    """
    Initializes the strike mark data and analyzers required for further processing.
    """
    global btc_day_analyzer, btc_year_analyzer

    # Fetch initial strike mark data
    get_all_strike_mark_data_threading()

    # Instantiate analyzers
    btc_day_analyzer = UnivariateSplineAnalyzer("BTC", "day")
    btc_year_analyzer = UnivariateSplineAnalyzer("BTC", "year")

    # Fetch initial Kalshi data after analyzers are ready
    fetch_and_save_kalshi_data()

    # send_email("The Arbitrager_9000 is up and running")


def fetch_and_save_kalshi_data():
    """
    Fetches Kalshi data and saves it to a JSON file.
    """
    try:
        # Fetch data using the initialized analyzers
        btc_max_day = get_kalshi_max_day_json("BTC", btc_day_analyzer)
        btc_max_year = get_kalshi_max_year_json("BTC", btc_year_analyzer)
        results = [btc_max_day, btc_max_year]

        # Save results to a JSON file
        if results:
            with open('kalshi_all_btc_markets_data.json', 'w') as f:
                json.dump({"data": results}, f, indent=4)

            # Refresh analyzer data
            btc_day_analyzer.refresh_data()
            btc_year_analyzer.refresh_data()
        else:
            print("No results found.")
        print("Updated Kalshi fetch")
    except Exception as e:
        print(f"Error fetching data: {e}")


# Initialize the scheduler
scheduler = BackgroundScheduler()

# Add periodic jobs
# scheduler.add_job(get_all_strike_mark_data_threading, 'interval', minutes=2)
# scheduler.add_job(fetch_and_save_kalshi_data, 'interval', minutes=2)
scheduler.add_job(
    get_all_strike_mark_data_threading,
    CronTrigger(minute='*/2', hour='9-16', timezone='US/Eastern')
)

scheduler.add_job(
    fetch_and_save_kalshi_data,
    CronTrigger(minute='*/2', hour='9-16', timezone='US/Eastern')
)

# Set up cron job for S3 merging and uploading
cron_trigger = CronTrigger(
    minute='30',
    hour='9-16',
    start_date='2025-01-01 09:30:00',
    timezone='US/Eastern'
)
scheduler.add_job(merge_and_upload_to_s3, cron_trigger)

# Start the scheduler
scheduler.start()


@app.route("/")
def hello():
    return "Hello, World!"


@app.route("/get_all_kalshi_markets_json")
def get_all_kalshi_markets_json():
    try:
        with open('kalshi_all_btc_markets_data.json', 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "Data file not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Error decoding JSON"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Initialize data before running the app
    initialize_data()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)), debug=True, use_reloader=False)
