from flask import Flask, render_template, request, redirect, url_for, make_response, flash, session
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Secret key for session management

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/voting_system"
mongo = PyMongo(app)


# Landing Page
@app.route('/')
def home():
    # Fetch the current voting results
    results = list(mongo.db.results.find())

    # Render the home page for both voters and admins
    return render_template('home.html', results=results)


# Admin Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if the admin exists in the database
        admin = mongo.db.admin.find_one({'username': username})

        if admin and admin['password'] == password:  # Compare plaintext passwords
            session['admin_logged_in'] = True  # Set admin session
            session['username'] = username
            return redirect(url_for('election_events'))
        else:
            flash("Invalid credentials. Please try again.", "danger")
            return render_template('login.html')

    return render_template('login.html')


# Voter Login
@app.route('/login_request', methods=['GET', 'POST'])
def login_request():
    if request.method == 'POST':
        voter_id = request.form.get('voterId')  # Retrieve voterId from the form

        # Check if the voter exists in the database using voterId
        voter = mongo.db.online_voters.find_one({'voterId': voter_id})

        if voter:  # If voterId matches an entry in the database
            session['voter_logged_in'] = True  # Set voter session
            session['username'] = voter['username']  # Store username in the session
            return redirect(url_for('voting_page'))
        else:
            flash("Invalid Voter ID. Please try again.", "danger")
            return render_template('voting_page.html')

    return render_template('voter_login.html')


# Logout
@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('home'))


# Election Events (Admin-Only)
@app.route('/election_events', methods=['GET', 'POST'])
def election_events():
    if not session.get('admin_logged_in'):  # Protect admin-only pages
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.form.to_dict()
        mongo.db.electionEvents.insert_one(data)
        flash("Election event added successfully.", "success")
        return redirect(url_for('election_events'))

    events = list(mongo.db.electionEvents.find())
    return render_template('election_event.html', events=events)


# Voting Page (Voter-Only)
@app.route('/voting_page', methods=['GET', 'POST'])
def voting_page():
    if not session.get('voter_logged_in'):
        return redirect(url_for('login_request'))  # Redirect to login if not logged in

    selected_election_id = None
    selected_candidates = []
    error_message = None  # Variable to store error message if user already voted

    if request.method == 'POST':
        # Get the selected election and candidate from the form
        selected_election_id = request.form.get('election')
        selected_candidate = request.form.get('candidates')

        if selected_candidate:
            # Check if the user has already voted in the selected election
            existing_vote = mongo.db.votes.find_one({
                'username': session.get('username'),
                'election_id': ObjectId(selected_election_id)
            })

            if existing_vote:
                # If the user has already voted, show an error message
                error_message = "You have already voted in this election."
            else:
                # Record the vote in the database if the user hasn't voted yet
                vote_data = {
                    'username': session.get('username'),
                    'election_id': ObjectId(selected_election_id),
                    'candidate': selected_candidate,
                    'vote_time': datetime.now()
                }
                mongo.db.votes.insert_one(vote_data)
                flash("Thank you for voting!", "success")
                return redirect(url_for('home'))

        # Fetch candidates for the selected election
        if selected_election_id:
            selected_election = mongo.db.election_type.find_one({'_id': ObjectId(selected_election_id)})
            selected_candidates = selected_election['candidates'] if selected_election else []

    # Retrieve all election events from the database
    elections = list(mongo.db.election_type.find())

    # Convert ObjectId to string for easy comparison in the template
    elections = [
        {**event, "_id": str(event["_id"])} for event in elections
    ]

    return render_template(
        'voting_page.html',
        elections=elections,
        selected_election_id=selected_election_id,
        selected_candidates=selected_candidates,
        error_message=error_message  # Pass the error message to the template
    )


# Online Voters Management (Admin-Only)
@app.route('/online_voters', methods=['GET', 'POST'])
def online_voters():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.form.to_dict()
        mongo.db.online_voters.insert_one(data)
        flash("Voter added successfully.", "success")
        return redirect(url_for('online_voters'))

    voters = list(mongo.db.online_voters.find())
    return render_template('online_voters.html', voters=voters)


# Polling Station Management (Admin-Only)
@app.route('/polling_station', methods=['GET', 'POST'])
def polling_station():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.form.to_dict()
        mongo.db.polling_station.insert_one(data)
        flash("Polling station added successfully.", "success")
        return redirect(url_for('polling_station'))

    stations = list(mongo.db.polling_station.find())
    return render_template('polling_station.html', stations=stations)

@app.route('/manage_polling_station', methods=['GET', 'POST'])
def manage_polling_station():
    if not session.get('admin_logged_in'):  # Ensure only admins can access
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Handle form submission
        selected_station_id = request.form.get('station_id')  # Get selected station ID
        if selected_station_id:
            # Update station data if needed
            station = mongo.db.polling_station.find_one({'_id': ObjectId(selected_station_id)})
            if station:
                flash(f"Selected station: {station['station_name']}", "success")

        else:
            # Add new station
            station_name = request.form.get('stationName')
            location = request.form.get('location')
            capacity = int(request.form.get('capacity'))

            mongo.db.polling_station.insert_one({
                'station_name': station_name,
                'location': location,
                'capacity': capacity,
                'votes': 0
            })
            flash("Polling station added successfully.", "success")
            return redirect(url_for('polling_station'))

    # Fetch all polling stations
    stations = list(mongo.db.polling_station.find())

    # Count votes dynamically
    for station in stations:
        vote_count = mongo.db.votes.count_documents({'station_id': station['_id']})
        station['votes'] = vote_count

    return render_template('manage_polling_station.html', stations=stations)



# Results Management (Admin-Only)
@app.route('/results', methods=['GET', 'POST'])
def results():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.form.to_dict()
        mongo.db.results.insert_one(data)
        flash("Result added successfully.", "success")
        return redirect(url_for('results'))

    results = list(mongo.db.results.find())
    return render_template('results.html', results=results)


if __name__ == '__main__':
    app.run(debug=True)
