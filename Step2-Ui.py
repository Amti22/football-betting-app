from flask import Flask, render_template, jsonify, request
import os
from datetime import datetime, timezone

app = Flask(__name__)

all_matches_file = 'matches/AllMatches.txt'  # Combined matches file

def read_matches(sport=None, date=None):
    matches = []
    current_time = datetime.now(timezone.utc)

    if not os.path.exists(all_matches_file):
        print(f"Error: '{all_matches_file}' does not exist.")
        return matches

    with open(all_matches_file, 'r') as file:
        lines = file.readlines()
        match_data = {}

        for line in lines:
            if line.startswith('==='):
                if match_data:
                    if (not sport or match_data.get('sport', '').lower() == sport.lower()) and \
                       (not date or match_data.get('start_date', '').startswith(date)):
                        start_date_str = match_data.get('start_date', '')
                        try:
                            date_object = datetime.fromisoformat(start_date_str)
                            match_data['formatted_date'] = date_object.strftime("%d/%m/%Y - %H:%M - %Z")
                            if date_object > current_time:
                                matches.append(match_data)
                        except ValueError:
                            print(f"Skipping invalid date: {start_date_str} (Match: {match_data.get('home_team')} vs {match_data.get('away_team')})")
                    match_data = {}
            elif line.startswith('Match:'):
                match_data['home_team'], match_data['away_team'] = line.split(': ')[1].strip().split(' vs ')
            elif line.startswith('Start Date:'):
                match_data['start_date'] = line.split(': ')[1].strip()
            elif line.startswith('Sport:'):
                match_data['sport'] = line.split(': ')[1].strip()
            elif line.startswith('Home Odds:'):
                match_data['home_odds'] = float(line.split(': ')[1].strip())
            elif line.startswith('Draw Odds:'):
                match_data['draw_odds'] = float(line.split(': ')[1].strip())
            elif line.startswith('Away Odds:'):
                match_data['away_odds'] = float(line.split(': ')[1].strip())

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
    return jsonify(matches)

@app.route('/sports')
def get_sports():
    sports = set()
    if not os.path.exists(all_matches_file):
        return jsonify([])

    with open(all_matches_file, 'r') as file:
        for line in file:
            if line.startswith('Sport:'):
                sports.add(line.split(': ')[1].strip())

    return jsonify(list(sports))

@app.route('/dates')
def get_dates():
    sport = request.args.get('sport')
    dates = set()
    if not os.path.exists(all_matches_file):
        return jsonify([])

    with open(all_matches_file, 'r') as file:
        match_data = {}

        for line in file:
            if line.startswith('==='):
                if match_data and (not sport or match_data.get('sport', '').lower() == sport.lower()):
                    date = match_data.get('start_date', '').split('T')[0]
                    dates.add(date)
                match_data = {}
            elif line.startswith('Sport:'):
                match_data['sport'] = line.split(': ')[1].strip()
            elif line.startswith('Start Date:'):
                match_data['start_date'] = line.split(': ')[1].strip()

    return jsonify(sorted(dates))

if __name__ == '__main__':
    app.run(debug=True)
