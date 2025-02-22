# Kalshi Trading Setup

Replace python with python3 in the following commands as needed

1. `cd server`: navigate to server directory
2. `venv python -m venv`: create a virtual environment in `server` directory ( or `python -m venv venv` for mac)
3. `venv/Scripts/activate`: activate the virtual environment (Windows) ( or `source ./venv/bin/activate` for mac)
4. `pip install -r requirements.txt`: to install dependencies from `requirements.txt` in the `server` directory
5. `export KALSHI_ACCESS_KEY=<your_key>`,  
   `export SENDGRID_API_KEY=<your_key>`,  
   `export AWS_ACCESS_KEY_ID=<your_key>`,  
   `export AWS_SECRET_ACCESS_KEY=<your_key>`,  
   `export BUCKET_NAME=<your_bucket_name>`,  
   `export AWS_REGION=<your_region>`,  
   Name your .key file `kalshi_key.key` and place it in the `server` directory
6. Navigate to `client` directory
7. `npm install`
8. change back to server directory, `python app.py`
9. open new terminal, goto client directory, `npm start`