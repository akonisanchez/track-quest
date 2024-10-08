from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import os
import datetime
import random

app = Flask(__name__)
app.secret_key = 'supersecretkey'  

# Config for SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trackstar.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login page if not authenticated

# Define the path to the CSV file
csv_file_path = '/Users/ajsanchez/sd_races/data/san_diego_race_data.csv'

# Load race data from CSV
def load_races_from_csv():
    if not os.path.exists(csv_file_path):
        print("CSV file not found. Please check the file path.")
        return []

    races = []
    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            races.append({
                'name': row['Race'],
                'date': row['Date'],
                'distance': row['Distance(s)'],
                'url': row['URL']
            })
    return races

# Load races into memory
races = load_races_from_csv()

@app.context_processor
def inject_year():
    return {'current_year': datetime.datetime.now().year}

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html', races=races)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)  # Hash the password
        
        db.session.add(new_user)
        db.session.commit() 
        
        flash('Registration successful!', 'success')
        return redirect(url_for('home'))
    
    return render_template('register.html')

@app.route('/races', methods=['GET'])
def display_races():
    selected_distance = request.args.get('distance')  
    unique_distances = sorted(set(distance.strip() for race in races for distance in race['distance'].split('/')))

    if selected_distance:
        filtered_races = [race for race in races if selected_distance in map(str.strip, race['distance'].split('/'))]
    else:
        filtered_races = races

    return render_template('races.html', races=filtered_races, selected_distance=selected_distance, distances=unique_distances)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/random_race')
def random_race():
    if races:
        random_race = random.choice(races)
        return redirect(random_race['url'])
    else:
        flash("No races available. Please check back later.", "error")
        return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)  # Provided by Flask-Login
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'danger')  
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()  # Provided by Flask-Login
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# Create tables when the application starts
with app.app_context():
    try:
        db.create_all()
        print("Database tables created!")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=9090)