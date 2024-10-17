from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, LoginManager, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import csv
import os
import datetime
import random

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Database configuration: Using SQLite for simplicity
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trackstar.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database, migration, and login manager
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Path to your CSV file with race data
csv_file_path = '/Users/ajsanchez/sd_races/data/san_diego_race_data.csv'

# Helper function to load race data from CSV
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

# Preload race data from the CSV
races = load_races_from_csv()

# Add the current year to every template
@app.context_processor
def inject_year():
    return {'current_year': datetime.datetime.now().year, 'datetime': datetime}

# Flask-Login: This function is needed to reload the user from the database
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Route for the home page
@app.route('/')
def home():
    return render_template('home.html', races=races)

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful!', 'success')
        return redirect(url_for('home'))
    
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            if not user.is_active:
                flash('You have been banned. Please contact support.', 'ban') # use ban category
                return redirect(url_for('login'))  # Redirect back to login page
            
            if user.check_password(password):
                login_user(user)
                flash('Logged in successfully!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid email or password', 'danger')
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

# Admin dashboard route: Only accessible by admin users
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('You do not have access to this page.', 'danger')
        return redirect(url_for('home'))
    users = User.query.all()
    return render_template('admin_dashboard.html', users=users)

# This decorator ensures only admin users can access certain routes
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You do not have access to this page.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Route to ban a user
@app.route('/ban_user/<int:user_id>', methods=['POST'])  # <-- Allow POST method
@admin_required
def ban_user(user_id):
    user_to_ban = User.query.get_or_404(user_id)
    user_to_ban.is_active = False
    db.session.commit()
    flash(f'User {user_to_ban.username} has been banned.', 'success')
    return redirect(url_for('admin_dashboard'))

# Route for user profile
@app.route('/profile')
@login_required
def profile():
    current_user.update_last_active()
    return render_template('profile.html', user=current_user)

# Route for updating "about me"
@app.route('/update_about_me', methods=['POST'])
@login_required
def update_about_me():
    about_me = request.form.get('about_me')
    current_user.about_me = about_me[:500]
    db.session.commit()
    flash('About Me section updated!', 'success')
    return redirect(url_for('profile'))

# Route to display races and filter them by distance
@app.route('/races', methods=['GET'])
def display_races():
    selected_distance = request.args.get('distance')
    unique_distances = sorted(set(distance.strip() for race in races for distance in race['distance'].split('/')))
    
    if selected_distance:
        filtered_races = [race for race in races if selected_distance in map(str.strip, race['distance'].split('/'))]
    else:
        filtered_races = races

    return render_template('races.html', races=filtered_races, selected_distance=selected_distance, distances=unique_distances)

# Route for random race selection
@app.route('/random_race')
def random_race():
    if races:
        random_race = random.choice(races)
        return redirect(random_race['url'])
    else:
        flash("No races available. Please check back later.", "error")
        return redirect(url_for('home'))

# Route for about page
@app.route('/about')
def about():
    return render_template('about.html')

# Route for contact page
@app.route('/contact')
def contact():
    return render_template('contact.html')

# ---- Database and User Model ----

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    join_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    about_me = db.Column(db.String(500), default='')
    last_active = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_last_active(self):
        self.last_active = datetime.datetime.utcnow()
        db.session.commit()

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