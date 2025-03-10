from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import config.aws_email_config as aws_email_config
from deribitAPIUtil import get_all_strike_mark_data_threading
import json
from kalshiAPIUtil import get_kalshi_max_day_json, get_kalshi_max_year_json
from flask_cors import CORS
from flask import Flask, jsonify
import os
from s3_update_util import merge_and_upload_to_s3
from univariateSplineAnalyzer import UnivariateSplineAnalyzer


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
    get_all_strike_mark_data_threading() # deribit

    # Instantiate analyzers
    btc_day_analyzer = UnivariateSplineAnalyzer("BTC", "day")
    btc_year_analyzer = UnivariateSplineAnalyzer("BTC", "year")

    # Fetch initial Kalshi data after analyzers are ready
    fetch_and_save_kalshi_data() # kalshi


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
        print(f"Error fetching kalshi data: {e}")


def fetch_deribit_and_kalshi_market_data():
    """
    CRON job that runs deribit then kalshi fetches sequentially.
    If deribit fails, we pause and wait until next cron job to run Kalshi fetch.
    """
    try:
        get_all_strike_mark_data_threading()
        # Only proceed to Kalshi fetch if Deribit fetch was successful
        fetch_and_save_kalshi_data()
    except Exception as e:
        print(f"Error in combined fetch job: {e}, will try again in 2 minutes")

def intialize_cron_jobs():
    # Initialize the scheduler
    scheduler = BackgroundScheduler()

    # Update scheduler jobs
    scheduler.add_job(
        fetch_deribit_and_kalshi_market_data,
        CronTrigger(minute='*/2', hour='9-16', timezone='US/Eastern')
    )

    if aws_email_config.ENABLE_S3_OPS:
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
    intialize_cron_jobs()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)), debug=True, use_reloader=False)
