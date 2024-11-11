# Standard library imports
import csv
import os
import datetime
import random

# Third-party imports
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import (
    login_user, logout_user, login_required, LoginManager, 
    current_user, UserMixin
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Float
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Application initialization
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # TODO: Move to environment variable

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/ajsanchez/sd_races/instance/trackquest_sd.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configuration constants
CSV_FILE_PATH = '/Users/ajsanchez/sd_races/data/san_diego_race_data.csv'

def load_races_from_csv():
    """
    Load race data from CSV file into memory.
    
    Returns:
        list: List of dictionaries containing race information with keys:
            - name: Race name
            - date: Race date
            - distance: Race distance(s)
            - url: Race website URL
    """
    if not os.path.exists(CSV_FILE_PATH):
        print("CSV file not found. Please check the file path.")
        return []

    races = []
    with open(CSV_FILE_PATH, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            races.append({
                'name': row['Race'],
                'date': row['Date'],
                'distance': row['Distance(s)'],
                'url': row['URL']
            })
    return races

# Preload race data
races = load_races_from_csv()

# Template context processors
@app.context_processor
def inject_year():
    """Inject current year into all templates."""
    return {'current_year': datetime.datetime.now().year, 'datetime': datetime}

# User authentication functions
@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))

# Authentication route handlers
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration with duplicate checking.
    
    Validates that username and email are unique before creating new user.
    Shows appropriate error messages if duplicates are found.
    """
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check for existing username
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            flash('That username is already taken. Please choose another.', 'error')
            return redirect(url_for('register'))
            
        # Check for existing email
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('An account with that email already exists. Please use a different email.', 'error')
            return redirect(url_for('register'))
        
        # If we get here, username and email are unique
        try:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            # Handle any other potential database errors
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login with ban check."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        print(f"Login attempt - Email: {email}")  # Debug print
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            print("User found in database")  # Debug print
            if not user.is_active:
                print("User is not active")  # Debug print
                flash('You have been banned. Please contact support.', 'ban')
                return redirect(url_for('login'))
            
            print(f"Checking password: {user.check_password(password)}")  # Debug print
            if user.check_password(password):
                login_user(user)
                flash('Logged in successfully!', 'success')
                return redirect(url_for('home'))
            else:
                print("Password check failed")  # Debug print
            
        flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

# Admin functionality
def admin_required(f):
    """
    Decorator to restrict routes to admin users only.
    Must be used after @login_required.
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You do not have access to this page.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard for user management."""
    if not current_user.is_admin:
        flash('You do not have access to this page.', 'danger')
        return redirect(url_for('home'))
    users = User.query.all()
    return render_template('admin_dashboard.html', users=users)

@app.route('/ban_user/<int:user_id>', methods=['POST'])
@admin_required
def ban_user(user_id):
    """Ban a user by ID."""
    user_to_ban = User.query.get_or_404(user_id)
    user_to_ban.is_active = False
    db.session.commit()
    flash(f'User {user_to_ban.username} has been banned.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/unban_user/<int:user_id>', methods=['POST'])
@admin_required
def unban_user(user_id):
    """Unban a user by ID."""
    user_to_unban = User.query.get_or_404(user_id)
    user_to_unban.is_active = True
    db.session.commit()
    flash(f'User {user_to_unban.username} has been unbanned.', 'success')
    return redirect(url_for('admin_dashboard'))

# User profile routes
@app.route('/profile')
@app.route('/profile/<username>')
@login_required
def profile(username=None):
    """
    Display user profile page.
    If username is provided, show that user's profile.
    If no username provided, show current user's profile.
    """
    if username:
        user = User.query.filter_by(username=username).first_or_404()
    else:
        user = current_user
        
    user.update_last_active()
    return render_template('profile.html', user=user)

@app.route('/update_about_me', methods=['POST'])
@login_required
def update_about_me():
    """Update user's about me section."""
    about_me = request.form.get('about_me')
    current_user.about_me = about_me[:500]  # Limit to 500 characters
    db.session.commit()
    flash('About Me section updated!', 'success')
    return redirect(url_for('profile'))

# Race management routes
@app.route('/races', methods=['GET'])
def display_races():
    """
    Display races with optional distance filtering and review data.
    Includes average ratings and review counts for each race.
    """
    selected_distance = request.args.get('distance')
    unique_distances = sorted(set(
        distance.strip() 
        for race in races 
        for distance in race['distance'].split('/')
    ))
    
    if selected_distance:
        filtered_races = [
            race for race in races 
            if selected_distance in map(str.strip, race['distance'].split('/'))
        ]
    else:
        filtered_races = races
        
    # Add review data to races
    races_with_reviews = []
    for race in filtered_races:
        avg_ratings, review_count = get_race_reviews(race['name'])
        race_data = race.copy()
        race_data.update({
            'avg_ratings': avg_ratings,
            'review_count': review_count
        })
        races_with_reviews.append(race_data)

    user_race_names = {race.race_name for race in current_user.races} if current_user.is_authenticated else set()

    return render_template(
        'races.html',
        races=races_with_reviews,
        selected_distance=selected_distance,
        distances=unique_distances,
        user_race_names=user_race_names
    )

@app.route('/add_race_to_profile', methods=['POST'])
@login_required
def add_race_to_profile():
    """Add a race to user's profile."""
    race_name = request.form['race_name']
    race_date = request.form['race_date']
    race_distance = request.form['race_distance']

    existing_race = UserRace.query.filter_by(
        user_id=current_user.id, 
        race_name=race_name
    ).first()
    
    if existing_race:
        flash('This race is already in your race list.', 'info')
        return redirect(url_for('display_races'))

    new_race = UserRace(
        user_id=current_user.id,
        race_name=race_name,
        race_date=race_date,
        race_distance=race_distance
    )
    db.session.add(new_race)
    db.session.commit()

    flash(f'{race_name} added to your race list!', 'success')
    return redirect(url_for('display_races'))

@app.route('/toggle_race_in_profile', methods=['POST'])
@login_required
def toggle_race_in_profile():
    """Toggle a race's presence in user's profile (add/remove)."""
    race_name = request.form['race_name']
    race_date = request.form['race_date']
    race_distance = request.form['race_distance']

    existing_race = UserRace.query.filter_by(
        user_id=current_user.id, 
        race_name=race_name
    ).first()

    if existing_race:
        db.session.delete(existing_race)
        db.session.commit()
        flash(f'{race_name} removed from your race list.', 'success')
    else:
        new_race = UserRace(
            user_id=current_user.id,
            race_name=race_name,
            race_date=race_date,
            race_distance=race_distance
        )
        db.session.add(new_race)
        db.session.commit()
        flash(f'{race_name} added to your race list!', 'success')
    
    return redirect(url_for('display_races'))

# Utility Routes
@app.route('/random_race')
def random_race():
    """Redirect to a random race's website."""
    if races:
        random_race = random.choice(races)
        return redirect(random_race['url'])
    else:
        flash("No races available. Please check back later.", "error")
        return redirect(url_for('home'))

@app.route('/about')
def about():
    """Display the about page."""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """Display the contact page."""
    return render_template('contact.html')

@app.route('/')
@app.route('/home')  # Adding an additional route path
def home():
    """
    Render home page with race listings.
    Accessible via both root URL ('/') and '/home'
    """
    return render_template('home.html', races=races)

@app.route('/past-races')
def past_races():
    """
    Display all historical races that have reviews but are no longer in the active races list.
    Orders races by most recently reviewed.
    """
    # Get all historical races that have reviews
    historical_races = (HistoricalRace.query
        .join(RaceReview)  # Only get races that have reviews
        .group_by(HistoricalRace.id)  # Group by race to avoid duplicates
        .order_by(db.func.max(RaceReview.review_date).desc())  # Order by most recent review
        .all())
    
    # For each race, get its review stats
    races_with_stats = []
    for race in historical_races:
        # Skip if race is in current active races list
        if any(r['name'] == race.name for r in races):
            continue
            
        avg_ratings, review_count = get_race_reviews(race.name)
        races_with_stats.append({
            'race': race,
            'avg_ratings': avg_ratings,
            'review_count': review_count,
            'latest_review': max(r.review_date for r in race.reviews)
        })
    
    return render_template('past_races.html', races=races_with_stats)

# Database Models
class User(db.Model, UserMixin):
    """
    User model for authentication and profile management.
    
    Attributes:
        id (int): Primary key
        username (str): Unique username
        email (str): Unique email address
        password_hash (str): Hashed password
        is_active (bool): Account status (True if not banned)
        join_date (datetime): Account creation date
        about_me (str): User's profile description
        last_active (datetime): Last activity timestamp
        is_admin (bool): Administrator status
    """
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
        """Hash and set user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def update_last_active(self):
        """Update user's last active timestamp."""
        self.last_active = datetime.datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<User {self.username}>'

class UserRace(db.Model):
    """
    Model for tracking races added by users.
    
    Attributes:
        user_id (int): Foreign key to User
        race_name (str): Name of the race
        race_date (str): Date of the race
        race_distance (str): Distance category
        is_completed (bool): Completion status
        finish_time (str): Race finish time (HH:MM:SS)
        race_notes (str): User notes about the race
        completion_date (datetime): When marked as completed
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    race_name = db.Column(db.String(150), nullable=False)
    race_date = db.Column(db.String(50), nullable=False)
    race_distance = db.Column(db.String(50), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    finish_time = db.Column(db.String(20))
    race_notes = db.Column(db.Text)
    completion_date = db.Column(db.DateTime)

    user = db.relationship('User', backref=db.backref('races', lazy=True))

    def is_future_race(self):
        """Check if race date is in the future."""
        race_date = datetime.datetime.strptime(self.race_date, '%Y-%m-%d')
        return race_date > datetime.datetime.now()

    def __repr__(self):
        return f'<UserRace {self.race_name}>'

class HistoricalRace(db.Model):
    """
    Model to store historical race information that persists even after races are removed from CSV.
    
    Attributes:
        id (int): Primary key
        name (str): Name of the race
        location (str): Race location (defaults to San Diego)
        race_date (str): Date when the race took place
        created_at (datetime): When this record was created
        reviews (relationship): One-to-many relationship with RaceReview model
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    location = db.Column(db.String(100), default='San Diego, CA')
    race_date = db.Column(db.String(50))  # New field to store race date
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    reviews = db.relationship('RaceReview', backref='historical_race', lazy=True)

    def __repr__(self):
        return f'<HistoricalRace {self.name}>'

class RaceReview(db.Model):
    """
    Model for storing user reviews and ratings of races.
    
    Attributes:
        user_id (int): Foreign key to User
        race_name (str): Name of reviewed race
        review_date (datetime): When review was posted
        race_year (int): Year the race was run
        distance (str): Race distance category
        overall_rating (float): Overall race rating (1-5)
        course_difficulty (float): Course difficulty rating (1-5)
        course_scenery (float): Scenery rating (1-5)
        race_production (float): Event organization rating (1-5)
        race_swag (float): Race merchandise rating (1-5)
        review_title (str): Review title
        review_text (str): Detailed review content
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    historical_race_id = db.Column(db.Integer, db.ForeignKey('historical_race.id'), nullable=False)
    review_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    race_year = db.Column(db.Integer, nullable=False)
    distance = db.Column(db.String(50), nullable=False)
    
    overall_rating = db.Column(Float, nullable=False)
    course_difficulty = db.Column(Float, nullable=False)
    course_scenery = db.Column(Float, nullable=False)
    race_production = db.Column(Float, nullable=False)
    race_swag = db.Column(Float, nullable=False)
    
    review_title = db.Column(db.String(50), nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    
    user = db.relationship('User', backref=db.backref('reviews', lazy=True))

    def __repr__(self):
        return f'<RaceReview {self.historical_race.name} by {self.user.username}>'

def get_or_create_historical_race(race_name, race_date=None):
    """
    Gets existing historical race record or creates new one if it doesn't exist.
    Now includes race date preservation.
    
    Args:
        race_name (str): Name of the race
        race_date (str): Date when the race takes place
        
    Returns:
        HistoricalRace: The historical race record
    """
    historical_race = HistoricalRace.query.filter_by(name=race_name).first()
    if not historical_race:
        historical_race = HistoricalRace(name=race_name, race_date=race_date)
        db.session.add(historical_race)
        db.session.commit()
    elif race_date and not historical_race.race_date:
        # Update existing record with date if it's missing
        historical_race.race_date = race_date
        db.session.commit()
    return historical_race

# Review-related functions and routes
def get_race_reviews(race_name):
    """
    Calculate average ratings and review count for a race using historical race record.
    
    Args:
        race_name (str): Name of the race
        
    Returns:
        tuple: (average_ratings dict, review_count int)
    """
    historical_race = HistoricalRace.query.filter_by(name=race_name).first()
    if not historical_race:
        return None, 0
    
    reviews = historical_race.reviews
    if not reviews:
        return None, 0
    
    avg_ratings = {
        'overall': sum(r.overall_rating for r in reviews) / len(reviews),
        'difficulty': sum(r.course_difficulty for r in reviews) / len(reviews),
        'scenery': sum(r.course_scenery for r in reviews) / len(reviews),
        'production': sum(r.race_production for r in reviews) / len(reviews),
        'swag': sum(r.race_swag for r in reviews) / len(reviews)
    }
    
    return avg_ratings, len(reviews)

@app.route('/review_race/<race_name>', methods=['GET'])
@login_required
def review_race(race_name):
    """Display race review form."""
    race = next((r for r in races if r['name'] == race_name), None)
    if not race:
        flash('Race not found.', 'error')
        return redirect(url_for('display_races'))
    
    distances = [d.strip() for d in race['distance'].split('/')]
    years = range(2021, 2026)
    
    return render_template(
        'review_race.html',
        race=race,
        distances=distances,
        years=years
    )

@app.route('/submit_review', methods=['POST'])
@login_required
def submit_review():
    """Handle race review submission with historical race preservation."""
    # Get race details from current races list
    race_name = request.form['race_name']
    current_race = next((r for r in races if r['name'] == race_name), None)
    race_date = current_race['date'] if current_race else None
    
    # Get or create historical race record with date
    historical_race = get_or_create_historical_race(race_name, race_date)
    
    # Create the review
    review = RaceReview(
        user_id=current_user.id,
        historical_race_id=historical_race.id,
        race_year=int(request.form['race_year']),
        distance=request.form['distance'],
        overall_rating=float(request.form['overall_rating']),
        course_difficulty=float(request.form['course_difficulty']),
        course_scenery=float(request.form['course_scenery']),
        race_production=float(request.form['race_production']),
        race_swag=float(request.form['race_swag']),
        review_title=request.form['review_title'],
        review_text=request.form['review_text']
    )
    
    if len(review.review_text) < 100:
        flash('Review text must be at least 100 characters.', 'error')
        return redirect(url_for('review_race', race_name=race_name))
    
    db.session.add(review)
    db.session.commit()
    
    flash('Your review has been submitted successfully!', 'success')
    return redirect(url_for('display_races'))

# Race completion routes
@app.route('/mark_race_complete/<int:race_id>', methods=['POST'])
@login_required
def mark_race_complete(race_id):
    """Mark a race as completed with finish time and notes."""
    race = UserRace.query.get_or_404(race_id)
    
    if race.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('profile'))
    
    race.is_completed = True
    race.completion_date = datetime.datetime.now()
    race.finish_time = request.form.get('finish_time')
    race.race_notes = request.form.get('race_notes')
    
    db.session.commit()
    flash('Race marked as completed!', 'success')
    return redirect(url_for('profile'))

@app.route('/update_race_details/<int:race_id>', methods=['POST'])
@login_required
def update_race_details(race_id):
    """Update details for a completed race."""
    race = UserRace.query.get_or_404(race_id)
    
    if race.user_id != current_user.id or not race.is_completed:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('profile'))
    
    race.finish_time = request.form.get('finish_time')
    race.race_notes = request.form.get('race_notes')
    
    db.session.commit()
    flash('Race details updated!', 'success')
    return redirect(url_for('profile'))

@app.route('/remove_race_from_profile/<int:race_id>', methods=['POST'])
@login_required
def remove_race_from_profile(race_id):
    """Remove a race from user's profile."""
    race_to_remove = UserRace.query.get_or_404(race_id)

    if race_to_remove.user_id != current_user.id:
        flash('You are not authorized to remove this race.', 'danger')
        return redirect(url_for('profile'))

    db.session.delete(race_to_remove)
    db.session.commit()

    flash(f'{race_to_remove.race_name} has been removed from your race list.', 'success')
    return redirect(url_for('profile'))

@app.route('/race_reviews/<race_name>')
def race_reviews(race_name):
    """Display all reviews for a specific race."""
    historical_race = HistoricalRace.query.filter_by(name=race_name).first_or_404()
    
    reviews = historical_race.reviews\
        .order_by(RaceReview.review_date.desc())\
        .all()
    
    avg_ratings, review_count = get_race_reviews(race_name)
    
    return render_template(
        'race_reviews.html',
        race_name=race_name,
        reviews=reviews,
        avg_ratings=avg_ratings,
        review_count=review_count
    )

# Database initialization
with app.app_context():
    try:
        db.create_all()  # Only create tables if they don't exist
        print("Database tables created!")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=9090)