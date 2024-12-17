from flask import Flask, render_template, jsonify, request
import os
from datetime import datetime, timedelta
from pytz import timezone, UTC, FixedOffset

app = Flask(__name__)

# Path to the new matches_output.txt file
matches_txt_file = 'matches_output.txt'


def read_matches(sport=None, date=None):
    matches = []
    current_time = datetime.now(UTC)

    if not os.path.exists(matches_txt_file):
        print(f"Error: '{matches_txt_file}' does not exist.")
        return matches

    # Read the text file line by line
    with open(matches_txt_file, 'r') as file:
        lines = file.readlines()

    for line in lines:
        row = line.strip().split(',')

        match_data = {}

        # Extract match details based on the structure of the file
        match_data['home_team'] = row[4]  # 'Team 1' is at index 4
        match_data['away_team'] = row[5]  # 'Team 2' is at index 5

        # Handle the Date and Time fields properly
        date_value = row[1]
        time_value = row[2]

        # If either date or time is missing or invalid, skip the match
        if date_value == 'N/A' or time_value == 'N/A' or not date_value or not time_value:
            print(f"Skipping invalid date or time: {date_value} {time_value} (Match: {match_data['home_team']} vs {match_data['away_team']})")
            continue

        # Correct the date and time format
        try:
            # Combine date and time properly
            start_date_str = date_value.strip() + ' ' + time_value.strip()  # Combine date and time
            print(f"Trying to parse date and time: {start_date_str}")  # Debugging line

            # Handle the case where there are two time values (e.g., '00:00:00 12:00:00')
            if len(start_date_str.split()) == 3:  # Case when the time format has two values
                start_date_str = start_date_str.split(' ')[0] + ' ' + start_date_str.split(' ')[1]  # Keep only the first time

            # Parse the date and time
            date_object = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')

            # If timezone info is available, apply it
            if len(row) > 3 and row[3] != 'N/A':  # Timezone field is at index 3
                tz_str = row[3].strip()
                try:
                    # Parse the UTC offset from the timezone string (e.g. +01:00)
                    offset_hours, offset_minutes = map(int, tz_str.split(':'))
                    tz = FixedOffset(offset_hours * 60 + offset_minutes)  # Using FixedOffset with timedelta
                    date_object = date_object.replace(tzinfo=tz)  # Apply timezone
                except ValueError:
                    print(f"Invalid timezone format: {tz_str}, skipping timezone parsing.")

            match_data['formatted_date'] = date_object.strftime("%d/%m/%Y - %H:%M - %Z")
            if date_object > current_time:
                matches.append(match_data)

        except ValueError as e:
            print(
                f"Skipping invalid date: {date_value} {time_value} (Match: {match_data['home_team']} vs {match_data['away_team']})")
            continue

        match_data['sport'] = row[6]  # 'Sport' is at index 6

        # Map the odds to more intuitive names
        match_data['odds'] = {
            'home_odds': row[15],  # Home team win odds at index 17 ('1X2 1')
            'draw_odds': row[16],  # Draw odds at index 18 ('1X2 X')
            'away_odds': row[17],  # Away team win odds at index 19 ('1X2 2')
            'bts_yes': row[8],  # BTS Yes odds at index 7
            'bts_no': row[9],  # BTS No odds at index 8
            'dc_1x': row[10],  # Double Chance Home/Draw at index 9 ('DC 1X')
            'dc_12': row[11],  # Double Chance Home/Away at index 10 ('DC 12')
            'dc_x2': row[12],  # Double Chance Draw/Away at index 11 ('DC X2')
            'dnb_1': row[13],  # Draw No Bet Home at index 12 ('DNB 1')
            'dnb_2': row[14],  # Draw No Bet Away at index 13 ('DNB 2')
            'ov_1d5': row[46],  # Double Chance Home/Draw at index 9 ('DC 1X')
            'ov_2d5': row[48],  # Double Chance Home/Away at index 10 ('DC 12')
            'ov_3d5': row[50],  # Double Chance Draw/Away at index 11 ('DC X2')
            'un_1d5': row[47],  # Double Chance Home/Draw at index 9 ('DC 1X')
            'un_2d5': row[49],  # Double Chance Home/Away at index 10 ('DC 12')
            'un_3d5': row[51],  # Double Chance Draw/Away at index 11 ('DC X2')
        }

    return matches


@app.route('/')
def index():
    # Render the main page where the matches will be displayed
    return render_template('index.html')


@app.route('/matches')
def get_matches():
    sport = request.args.get('sport')
    date = request.args.get('date')
    matches = read_matches(sport, date)
    print(f"Matches found: {len(matches)}")  # Debugging line
    return jsonify(matches)


@app.route('/sports')
def get_sports():
    sports = set()
    if not os.path.exists(matches_txt_file):
        return jsonify([])

    # Read the text file line by line
    with open(matches_txt_file, 'r') as file:
        lines = file.readlines()

    # Extract the sports
    for line in lines:
        row = line.strip().split(',')
        if 'N/A' in row or len(row) < 20:
            continue
        sports.add(row[6])  # 'Sport' is at index 6

    return jsonify(list(sports))


@app.route('/dates')
def get_dates():
    sport = request.args.get('sport')
    dates = set()
    if not os.path.exists(matches_txt_file):
        return jsonify([])

    # Read the text file line by line
    with open(matches_txt_file, 'r') as file:
        lines = file.readlines()

    # Add dates
    for line in lines:
        row = line.strip().split(',')
        if 'N/A' in row or len(row) < 20:
            continue
        if sport and row[6].lower() != sport.lower():  # Filter by sport if specified
            continue
        dates.add(row[1])  # 'Date' is at index 1

    return jsonify(sorted(dates))


if __name__ == '__main__':
    app.run(debug=True)
