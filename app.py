# Import necessary modules
from flask import Flask, render_template, request, flash
import csv
import os

# Create a Flask app instance
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Secret key for session management

# Define the path to the CSV file
csv_file_path = '/Users/ajsanchez/sd_races/data/san_diego_race_data.csv'

def load_races_from_csv():
    # Load race data from a CSV file
    if not os.path.exists(csv_file_path):
        print("CSV file not found. Please check the file path.")
        return []

    races = []
    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Update the column names to match the CSV headers
            races.append({
                'name': row['Race'],  # Use 'Race' instead of 'name'
                'date': row['Date'],  # Use 'Date' instead of 'date'
                'distance': row['Distance(s)'],  # Use 'Distance(s)' instead of 'distance'
                'url': row['URL']  # Include the URL
            })
    return races

# Load race data from the CSV file when the app starts
races = load_races_from_csv()  # Load races into memory

# Define the homepage route (URL)
@app.route('/')
def home():
    return render_template('home.html', races=races)  # Pass the race data to the template

# Define the Find a Race route
@app.route('/races', methods=['GET'])
def display_races():
    selected_distance = request.args.get('distance')  # Get selected distance from query params

    # Get unique distances from the loaded races
    unique_distances = sorted(set(
    distance.strip() for race in races for distance in race['distance'].split('/')  #  Split by '/' for multiple distances
))  # Uses a set to get unique distances and sort them

    if selected_distance:
        # Filter races that include the selected distance (case-insensitive)
        filtered_races = [race for race in races if selected_distance in map(str.strip, race['distance'].split('/'))]
    else:
        filtered_races = races  # Get all races if no filter is applied

    return render_template('races.html', races=filtered_races, selected_distance=selected_distance, distances=unique_distances)

# Define about route
@app.route('/about')
def about():
    return render_template('about.html')  # Ensure you have an about.html template

# Define contact route
@app.route('/contact')
def contact():
    return render_template('contact.html')  # Make sure this template exists in the templates directory

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True, port=9090)  # Start the Flask app in debug mode on port 9090
