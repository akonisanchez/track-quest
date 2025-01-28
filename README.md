# TrackQuest SD

TrackQuest SD is a web application that helps runners discover and review races in San Diego. Users can explore upcoming races, read reviews from fellow runners, and track their race participation by editing their unique profile.

![Home](static/home.png)

## Tech Stack
### Backend
- Python/Flask - RESTful API development
- SQLite - Database management
- SQLAlchemy ORM - Database modeling and migrations
- Flask-Login - User authentication
- Werkzeug - Security and password hashing
- Flask-Migrate - Database migrations
- Pandas - Data processing
- BeautifulSoup4 - Web scraping race data

### Frontend
- HTML/CSS - Responsive design
- JavaScript - Dynamic interactions
- React - Interactive Past Races page
- Jinja2 - Template engine
- TailwindCSS - Utility-first CSS

## Features

### Race Discovery
- Browse upcoming San Diego races

![Find Race](static/find_race.gif)

- Filter races by distance

![Filter](static/race_filter.gif)

- Random race selector:
  - Ready to take on any challenge? Use the **random race** button to be redirected to the registration page of a random race that is upcoming. Perfect if you want to test your endurance across any event!

![Random](static/random_race.gif)
 
- View past race reviews and ratings

![Past Races](static/past_races.gif)

### User Features
- User authentication and profiles

![Profile](static/profile.gif)

- Personal race tracking (upcoming and completed)
- Race review system with ratings
- Photo upload capability for race reviews

### Review System
- Rate races on multiple criteria (difficulty, scenery, etc.)
- View aggregated ratings
- Upload race photos
- Edit/delete your reviews

## Setup and Installation

1. Clone the repository
```bash
git clone [https://github.com/akonisanchez/track-quest.git]
```

2. Create and activate virtual environment
```bash
python -m venv venv (might need to do 'python3')
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Run the application
```bash
python app.py (might need to do 'python3')
```

Access the application at `http://localhost:9090`

## Usage

- Create an account to start tracking races

![register](static/register.gif)

- Browse available races on the "Find a Race" page
- Read reviews on the "Find a Race" and "Past Races" pages

![View Reviews](static/view_reviews.gif)

- Add races you plan to compete in to your profile

![Add Race List](static/add_race_list.gif)

-Update your performance as you complete each race

![Update Race Performance](static/update_race_performance.gif)

- Write reviews for races you've completed

![Review Race](static/add_race_review.gif)
