from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
from pytz import UTC, FixedOffset
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import base64
import json
import tempfile
from flask import Flask, render_template, jsonify, request
from datetime import datetime
from pytz import FixedOffset, UTC
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import requests


# Flask app setup
app = Flask(__name__)

# Google Sheets configuration
SPREADSHEET_ID = '1ZV-oZTpSee2xF0BET84SsAtpTQPLsm0fhZDKfd18E00'

RANGE_NAME = 'Sheet1!A:CF'  # Adjust based on your sheet's data range
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_FILE = 'credentials.json'
ENCODED_CREDENTIALS_FILE = 'Credentials-Encoded.json'

# Discord Webhook Configuration
DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1322269431761604760/JqbwTRPdxX0EZ_oqrhJJhrfZRBkVwlt7-0pvH4bHeQHTl9rJovSc3kRvnIAp-ae6dgx_'

# Load credentials and create a Sheets API client
credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
sheets_service = build('sheets', 'v4', credentials=credentials)


from datetime import datetime
from pytz import FixedOffset, UTC

# Function to send a message to Discord
def send_bet_to_discord(bet_details):
    try:
        bet_message = (
            f"**Bet placed on {bet_details['selectedOption'].capitalize()}**\n"
            f"Odds: {bet_details['selectedOdds']}\n"
            f"Amount: ${bet_details['betAmountUSD']} (approx. £{bet_details['betAmountGBP']} GBP)\n\n"
            f"**Match**: {bet_details['homeTeam']} vs {bet_details['awayTeam']}\n"
            f"**Date**: {bet_details['matchDate']}\n"
            f"**Bet placed at**: {bet_details['currentDateTime']}\n"
        )

        # Sending the message to Discord via webhook
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": bet_message})
        if response.status_code == 204:
            print("Message successfully sent to Discord.")
        else:
            print(f"Failed to send message. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending bet details to Discord: {e}")

# Endpoint to save the bet details
@app.route('/save_bet', methods=['POST'])
def save_bet():
    try:
        # Get the bet details from the request
        bet_details = request.get_json()

        # Prepare the bet details to be sent to Discord
        send_bet_to_discord(bet_details)

        return 'Bet details sent to Discord successfully', 200
    except Exception as e:
        return f"Error saving bet details: {e}", 500


# Function to decode the credentials and use them
def decode_credentials():
    try:
        # Read the encoded credentials from the JSON file
        with open(ENCODED_CREDENTIALS_FILE, 'r') as f:
            encoded_data = json.load(f)

        # Decode the base64 encoded credentials
        encoded_credentials = encoded_data.get('encoded_credentials')
        if not encoded_credentials:
            raise ValueError("No encoded credentials found in the file")

        decoded_credentials = base64.b64decode(encoded_credentials)

        # Create a temporary file to store the decoded credentials
        with tempfile.NamedTemporaryFile(delete=False, mode='wb') as temp_file:
            temp_file.write(decoded_credentials)
            temp_file_path = temp_file.name

        return temp_file_path

    except Exception as e:
        print(f"Error decoding credentials: {e}")
        return None

def fetch_matches_from_sheets():
    try:
        sheets_service = create_sheets_service()
        if not sheets_service:
            print("Failed to create Sheets API service.")
            return []

        # Fetch the data from the Google Sheet
        sheet = sheets_service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        rows = result.get('values', [])

        matches = []
        current_time = datetime.now(UTC)

        for index, row in enumerate(rows):
            print(f"Processing row {index}, total columns: {len(row)}")

            # Skip rows that don't have the expected number of columns
            if len(row) < 20 or 'N/A' in row:
                continue

            match_data = {
                'home_team': row[4],  # Adjust indices based on your sheet structure
                'away_team': row[5],
                'sport': row[6],
                'odds': {
                    'home_odds': row[15],
                    'draw_odds': row[16],
                    'away_odds': row[17],
                    'bts_yes': row[8],
                    'bts_no': row[9],
                    'dc_1x': row[10],
                    'dc_12': row[11],
                    'dc_x2': row[12],
                    'dnb_1': row[13],
                    'dnb_2': row[14],
                    'ov_1d5': row[78] if len(row) > 78 else None,
                    'ov_2d5': row[80] if len(row) > 80 else None,
                    'ov_3d5': row[82] if len(row) > 82 else None,
                    'un_1d5': row[79] if len(row) > 79 else None,
                    'un_2d5': row[81] if len(row) > 81 else None,
                    'un_3d5': row[80] if len(row) > 80 else None,

                    'ah1_m3d75': row[18],  # AH 1 -3.75
                    'ah2_m3d75': row[19],  # AH 2 -3.75
                    'ah1_m3d5': row[20],   # AH 1 -3.5
                    'ah2_m3d5': row[21],   # AH 2 -3.5
                    'ah1_m3d25': row[22],  # AH 1 -3.25
                    'ah2_m3d25': row[23],  # AH 2 -3.25
                    'ah1_m3': row[24],     # AH 1 -3.0
                    'ah2_m3': row[25],     # AH 2 -3.0

                    'ah1_m2d75': row[26],  # AH 1 -2.75
                    'ah2_m2d75': row[27],  # AH 2 -2.75
                    'ah1_m2d5': row[28],   # AH 1 -2.5
                    'ah2_m2d5': row[29],   # AH 2 -2.5
                    'ah1_m2d25': row[30],  # AH 1 -2.25
                    'ah2_m2d25': row[31],  # AH 2 -2.25
                    'ah1_m2': row[32],     # AH 1 -2.0
                    'ah2_m2': row[33],     # AH 2 -2.0

                    'ah1_m1d75': row[34],  # AH 1 -1.75
                    'ah2_m1d75': row[35],  # AH 2 -1.75
                    'ah1_m1d5': row[36],   # AH 1 -1.5
                    'ah2_m1d5': row[37],   # AH 2 -1.5
                    'ah1_m1d25': row[38],  # AH 1 -1.25
                    'ah2_m1d25': row[39],  # AH 2 -1.25
                    'ah1_m1': row[40],     # AH 1 -1.0
                    'ah2_m1': row[41],     # AH 2 -1.0

                    'ah1_m0d75': row[42],  # AH 1 -0.75
                    'ah2_m0d75': row[43],  # AH 2 -0.75
                    'ah1_m0d5': row[44],   # AH 1 -0.5
                    'ah2_m0d5': row[45],   # AH 2 -0.5
                    'ah1_m0d25': row[46],  # AH 1 -0.25
                    'ah2_m0d25': row[47],  # AH 2 -0.25
                    'ah1_m0': row[48],     # AH 1 0.0
                    'ah2_m0': row[49],     # AH 2 0.0

                    'ah1_p1d75': row[50],  # AH 1 +0.75
                    'ah2_p1d75': row[51],  # AH 2 +0.75
                    'ah1_p1d5': row[52],   # AH 1 +1.5
                    'ah2_p1d5': row[53],   # AH 2 +1.5
                    'ah1_p1d25': row[54],  # AH 1 +1.25
                    'ah2_p1d25': row[55],  # AH 2 +1.25
                    'ah1_p1': row[56],     # AH 1 +1.0
                    'ah2_p1': row[57],     # AH 2 +1.0

                    'ah1_p2d75': row[58],  # AH 1 +2.75
                    'ah2_p2d75': row[59],  # AH 2 +2.75
                    'ah1_p2d5': row[60],   # AH 1 +2.5
                    'ah2_p2d5': row[61],   # AH 2 +2.5
                    'ah1_p2d25': row[62],  # AH 1 +2.25
                    'ah2_p2d25': row[63],  # AH 2 +2.25
                    'ah1_p2': row[64],     # AH 1 +2.0
                    'ah2_p2': row[65],     # AH 2 +2.0

                    'ah1_p3d5': row[76],   # AH 1 +3.5
                    'ah2_p3d5': row[77],   # AH 2 +3.5
                    'ah1_p3d25': row[74],  # AH 1 +3.25
                    'ah2_p3d25': row[75],  # AH 2 +3.25
                    'ah1_p3': row[72],     # AH 1 +3.0
                    'ah2_p3': row[73]      # AH 2 +3.0


                }
            }

            # Parse date and time
            try:
                date_value = row[1]
                time_value = row[2]
                if date_value == 'N/A' or time_value == 'N/A':
                    continue

                start_date_str = f"{date_value.strip()} {time_value.strip()}"
                date_object = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')

                if len(row) > 3 and row[3] != 'N/A':  # Parse timezone
                    offset_hours, offset_minutes = map(int, row[3].split(':'))
                    tz = FixedOffset(offset_hours * 60 + offset_minutes)
                    date_object = date_object.replace(tzinfo=tz)

                if date_object > current_time:
                    match_data['formatted_date'] = date_object.strftime("%d/%m/%Y - %H:%M - %Z")
                    matches.append(match_data)

            except ValueError as e:
                print(f"Error parsing date/time: {e}")
                continue

        return matches

    except Exception as e:
        print(f"Error fetching data from Google Sheets: {e}")
        return []

# Load credentials and create a Sheets API client
def create_sheets_service():
    credentials_path = decode_credentials()
    if credentials_path:
        credentials = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
        sheets_service = build('sheets', 'v4', credentials=credentials)
        return sheets_service
    return None


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/football')
def football():
    return render_template('index-Football.html')

@app.route('/basketball')
def basketball():
    return render_template('index-Basketball.html')



@app.route('/matches')
def get_matches():
    sport = request.args.get('sport')
    date = request.args.get('date')
    matches = fetch_matches_from_sheets()

    # Filter by sport and date
    if sport:
        matches = [match for match in matches if match['sport'].lower() == sport.lower()]
    if date:
        matches = [match for match in matches if match['formatted_date'].startswith(date)]

    return jsonify(matches)


@app.route('/sports')
def get_sports():
    matches = fetch_matches_from_sheets()
    sports = {match['sport'] for match in matches}
    return jsonify(list(sports))


@app.route('/dates')
def get_dates():
    sport = request.args.get('sport')
    matches = fetch_matches_from_sheets()

    if sport:
        matches = [match for match in matches if match['sport'].lower() == sport.lower()]

    dates = {match['formatted_date'].split(' - ')[0] for match in matches}
    return jsonify(sorted(dates))


if __name__ == '__main__':
    app.run(debug=True)
