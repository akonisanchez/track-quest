// static/js/pastRaces.js

// RatingBar component stays the same
const RatingBar = ({ label, value }) => {
    const percentage = (value / 5) * 100;
    return (
        <div className="rating-bar-item">
            <span className="rating-label">{label}</span>
            <div className="rating-progress">
                <div className="rating-fill" style={{ width: `${percentage}%` }}></div>
                <span className="rating-value">{value.toFixed(1)}</span>
            </div>
        </div>
    );
};

const RaceCard = ({ race }) => {
    return (
        <div className="race-card">
            <div className="race-header">
                <h2>{race.name}</h2>
                <div className="overall-rating">
                    <span className="star">★</span>
                    <span>{race.averageRating.toFixed(1)}</span>
                    <span className="review-count">({race.reviewCount} reviews)</span>
                </div>
            </div>

            <div className="rating-bars">
                <RatingBar label="Course Difficulty" value={race.ratings.difficulty} />
                <RatingBar label="Scenery" value={race.ratings.scenery} />
                <RatingBar label="Race Production" value={race.ratings.production} />
                <RatingBar label="Race Swag" value={race.ratings.swag} />
            </div>

            <div className="card-actions">
                <a href={`/race_reviews/${race.name}`} className="read-btn">Read Reviews</a>
                <a href={`/review_race/${race.name}`} className="write-btn">Write Review</a>
            </div>

            <div className="last-reviewed">
                Last reviewed: {new Date(race.lastReviewed).toLocaleDateString()}
            </div>
        </div>
    );
};

const PastRaces = () => {
    const [races, setRaces] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState(null);

    React.useEffect(() => {
        fetch('/api/past-races')
            .then(response => response.json())
            .then(data => {
                console.log("Received data:", data);
                setRaces(data);
                setLoading(false);
            })
            .catch(error => {
                console.error('Error:', error);
                setError(error.toString());
                setLoading(false);
            });
    }, []);

    if (loading) {
        return <div className="loading">Loading races...</div>;
    }

    if (error) {
        return <div className="error">Error loading races: {error}</div>;
    }

    if (!races.length) {
        return <div className="no-races">No past races found</div>;
    }

    return (
        <div className="past-races-container">
            <div className="hero-section">
                <h1>Past Race Reviews</h1>
                <p>Explore runner experiences from previous events</p>
            </div>

            <div className="race-grid">
                {races.map((race, index) => (
                    <RaceCard key={index} race={race} />
                ))}
            </div>
        </div>
    );
};

ReactDOM.render(
    <PastRaces />,
    document.getElementById('react-past-races')
);