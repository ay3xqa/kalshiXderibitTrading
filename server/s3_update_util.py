from dotenv import load_dotenv
import boto3
import os
import csv
import time
import pandas as pd
import json

load_dotenv()


AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')
BUCKET_NAME = os.getenv('BUCKET_NAME')
S3_FILE_NAME = "kalshi-historical.csv"
LOCAL_FILE_NAME = "kalshi-hourly-data.csv"
S3_FILE_NAME_GENERIC = "kalshi-historical-generic.csv"
LOCAL_FILE_NAME_GENERIC = "kalshi-hourly-data-generic.csv"

s3 = boto3.client('s3',
                  aws_access_key_id=AWS_ACCESS_KEY,
                  aws_secret_access_key=AWS_SECRET_KEY,
                  region_name=AWS_REGION)


def download_file_from_s3():
    try:
        local_file = "kalshi-historical.csv"  
        s3.download_file(BUCKET_NAME, S3_FILE_NAME, local_file)
        print(f"Downloaded {S3_FILE_NAME} from {BUCKET_NAME} to {local_file}")

        local_file_generic = "kalshi-historical-generic.csv"  
        s3.download_file(BUCKET_NAME, S3_FILE_NAME_GENERIC, local_file_generic)
        print(f"Downloaded {S3_FILE_NAME_GENERIC} from {BUCKET_NAME} to {local_file_generic}")
    except Exception as e:
        print(f"Error downloading file: {e}")

def merge_and_upload_helper(storage_type):
    if storage_type == "generic":
        local_file_name = LOCAL_FILE_NAME_GENERIC
        s3_file_name = S3_FILE_NAME_GENERIC
        col_name = "deribit_stats_serialized"
    else:
        local_file_name = LOCAL_FILE_NAME
        s3_file_name = S3_FILE_NAME
        col_name = 'pdf_estimate'

    historical_df = pd.read_csv(s3_file_name)
    
    hourly_column_names = ['time', 'currency', 'event_type', 'contract_type', 'strike_price', col_name, 'current_kalshi_price']
    hourly_df = pd.read_csv(local_file_name, header=None, names=hourly_column_names)
    
    merged_df = pd.concat([historical_df, hourly_df], ignore_index=True)
    
    merged_df.to_csv(s3_file_name, index=False)
    
    s3.upload_file(s3_file_name, BUCKET_NAME, s3_file_name)
    
    with open(local_file_name, 'w') as f:
        f.truncate(0)
    os.remove(s3_file_name)
    print(f"Merged and uploaded data to S3 successfully. Cleared local {local_file_name} file")

def merge_and_upload_to_s3():
    try:
        download_file_from_s3()
        merge_and_upload_helper("generic")
        merge_and_upload_helper("custom")

    except Exception as e:
        print(f"Error during merge and upload: {e}")

def load_json_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return json.dumps(data["data"])  # Convert the "data" list to a JSON string

def update_local_csv(timestamp, currency, event_type, contract_type, strike_price, pdf_estimate, current_kalshi):
    deribit_stats_json = load_json_data("data/BTC_day_strike_mark_data.json")  # Load and serialize JSON
    row_generic = [timestamp, currency, event_type, contract_type, strike_price, deribit_stats_json, current_kalshi]
    row = [timestamp, currency, event_type, contract_type, strike_price, pdf_estimate, current_kalshi]
 
    with open(LOCAL_FILE_NAME_GENERIC, mode='a', newline='') as file:

        writer = csv.writer(file)
        try:
            writer.writerow(row_generic)

        except Exception as e:
            print(f"Error appending row generic: {e}")

    with open(LOCAL_FILE_NAME, mode='a', newline='') as file:
        writer = csv.writer(file)
        try:
            writer.writerow(row)     
        except Exception as e:
            print(f"Error appending row: {e}")

