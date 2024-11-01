from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, LoginManager, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Float #####
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

# Route to unban user
@app.route('/unban_user/<int:user_id>', methods=['POST'])
@admin_required
def unban_user(user_id):
    user_to_unban = User.query.get_or_404(user_id)
    user_to_unban.is_active = True # Set the user to active
    db.session.commit()
    flash(f'User {user_to_unban.username} has been unbanned.', 'success')
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
        
    # Add review data to each race
    races_with_reviews = []
    for race in filtered_races:
        # Get the average ratings and review count
        avg_ratings, review_count = get_race_reviews(race['name'])
        # Create a new dictionary with all race info plus review data
        race_data = race.copy()
        race_data['avg_ratings'] = avg_ratings
        race_data['review_count'] = review_count
        races_with_reviews.append(race_data)

    # Fetch races already added to current user's race list
    user_race_names = {race.race_name for race in current_user.races} if current_user.is_authenticated else set()

    # Pass the enhanced race data to the template
    return render_template(
        'races.html',
        races=races_with_reviews,  # Use the enhanced race data instead of filtered_races
        selected_distance=selected_distance,
        distances=unique_distances,
        user_race_names=user_race_names
    )

@app.route('/add_race_to_profile', methods=['POST'])
@login_required
def add_race_to_profile():
    race_name = request.form['race_name']
    race_date = request.form['race_date']
    race_distance = request.form['race_distance']

    # Check if the race is already in the user's list
    existing_race = UserRace.query.filter_by(user_id=current_user.id, race_name=race_name).first()
    if existing_race:
        flash('This race is already in your race list.', 'info')
        return redirect(url_for('display_races'))

    # Add new race to the user's race list
    new_race = UserRace(user_id=current_user.id, race_name=race_name, race_date=race_date, race_distance=race_distance)
    db.session.add(new_race)
    db.session.commit()

    flash(f'{race_name} added to your race list!', 'success')
    return redirect(url_for('display_races'))

# Route to toggle adding/removing a race in the user's race list
@app.route('/toggle_race_in_profile', methods=['POST'])
@login_required
def toggle_race_in_profile():
    race_name = request.form['race_name']
    race_date = request.form['race_date']
    race_distance = request.form['race_distance']

    # Check if the race is already in the user's list
    existing_race = UserRace.query.filter_by(
        user_id=current_user.id, 
        race_name=race_name
    ).first()

    if existing_race:
        # Remove race if it exists
        db.session.delete(existing_race)
        db.session.commit()
        flash(f'{race_name} removed from your race list.', 'success')
    else:
        # Add race if it does not exist
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

# New table to track the races added by users
class UserRace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    race_name = db.Column(db.String(150), nullable=False)
    race_date = db.Column(db.String(50), nullable=False)
    race_distance = db.Column(db.String(50), nullable=False)
  # fields for race completion tracking
    is_completed = db.Column(db.Boolean, default=False)  # Track if race is completed
    finish_time = db.Column(db.String(20))  # Store finish time as HH:MM:SS
    race_notes = db.Column(db.Text)  # Store race experience notes
    completion_date = db.Column(db.DateTime)  # When the race was marked as completed

    user = db.relationship('User', backref=db.backref('races', lazy=True))

    def __repr__(self):
        return f'<UserRace {self.race_name}>'

 # Helper method to determine if race is in the future
    def is_future_race(self):
        """Check if race date is in the future"""
        race_date = datetime.datetime.strptime(self.race_date, '%Y-%m-%d')
        return race_date > datetime.datetime.now()
    
#####
class RaceReview(db.Model):
    """
    Model for storing race reviews from users.
    Each review is associated with a specific race and user.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    race_name = db.Column(db.String(150), nullable=False)
    review_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)  # Changed this line
    race_year = db.Column(db.Integer, nullable=False)
    distance = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), default='San Diego, CA')
    
    # Rating fields (1-5 scale)
    overall_rating = db.Column(Float, nullable=False)
    course_difficulty = db.Column(Float, nullable=False)
    course_scenery = db.Column(Float, nullable=False)
    race_production = db.Column(Float, nullable=False)
    race_swag = db.Column(Float, nullable=False)
    
    # Review content
    review_title = db.Column(db.String(50), nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('reviews', lazy=True))
    
    def __repr__(self):
        return f'<RaceReview {self.race_name} by {self.user.username}>'
####
def get_race_reviews(race_name):
    """
    Get all reviews and calculate average ratings for a race.
    Returns a tuple of (average_ratings, review_count)
    """
    reviews = RaceReview.query.filter_by(race_name=race_name).all()
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
 
 ####
@app.route('/review_race/<race_name>', methods=['GET'])
@login_required
def review_race(race_name):
    """
    Display the race review form for a specific race.
    """
    # Get race details from your races list
    race = next((r for r in races if r['name'] == race_name), None)
    if not race:
        flash('Race not found.', 'error')
        return redirect(url_for('display_races'))
      
       # Get distances from the race
    distances = [d.strip() for d in race['distance'].split('/')]
     
       # Generate year choices (2021-2025)
    years = range(2021, 2026)
    
    return render_template(
        'review_race.html',
        race=race,
        distances=distances,
        years=years
    )

####
@app.route('/submit_review', methods=['POST'])
@login_required
def submit_review():
    """
    Handle the submission of a race review.
    """
    # Create new review object
    review = RaceReview(
        user_id=current_user.id,
        race_name=request.form['race_name'],
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
    
    # Validate review text length
    if len(review.review_text) < 100:
        flash('Review text must be at least 100 characters.', 'error')
        return redirect(url_for('review_race', race_name=review.race_name))
    
    # Save review
    db.session.add(review)
    db.session.commit()
    
    flash('Your review has been submitted successfully!', 'success')
    return redirect(url_for('display_races'))

@app.route('/mark_race_complete/<int:race_id>', methods=['POST'])
@login_required
def mark_race_complete(race_id):
    """
    Mark a race as completed and optionally add finish time and notes
    """
    race = UserRace.query.get_or_404(race_id)
    
    # Verify user owns this race
    if race.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('profile'))
    
    # Update race completion details
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
    """
    Update finish time and notes for a completed race
    """
    race = UserRace.query.get_or_404(race_id)
    
    # Verify user owns this race and it's completed
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
    race_to_remove = UserRace.query.get_or_404(race_id)

    if race_to_remove.user_id != current_user.id:
        flash('You are not authorized to remove this race.', 'danger')
        return redirect(url_for('profile'))

    db.session.delete(race_to_remove)
    db.session.commit()

    flash(f'{race_to_remove.race_name} has been removed from your race list.', 'success')
    return redirect(url_for('profile'))

#####
@app.route('/race_reviews/<race_name>')
def race_reviews(race_name):
    """
    Display all reviews for a specific race.
    """
    reviews = RaceReview.query.filter_by(race_name=race_name)\
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

# Create tables when the application starts
with app.app_context():
    try:
        db.create_all()
        print("Database tables created!")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=9090)