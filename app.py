from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os # For managing file paths

# --- Flask Application Setup ---
app = Flask(__name__)

# Configure the database
# We're using SQLite, so specify the path to the database file.
# 'instance' folder is a good place for local data like databases.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # To suppress a warning

# Ensure the instance folder exists for the database file
os.makedirs(app.instance_path, exist_ok=True)

# Initialize the database
db = SQLAlchemy(app)

# --- Database Model Definition ---
# This defines the structure of our 'road_clearing_request' table
class RoadClearingRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.String(50), unique=True, nullable=False) # e.g., RC-2023-001
    reporter_name = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(20), nullable=True)
    barangay = db.Column(db.String(100), nullable=False)
    street_address = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='Pending') # e.g., Pending, In Progress, Completed
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Request {self.request_id} - {self.reporter_name} - {self.status}>"

# --- Create Database Tables ---
# This needs to be called once to create the tables based on our models.
# It's good practice to put this in a separate script or a CLI command for production,
# but for development, we can run it within the app's context.
with app.app_context():
    db.create_all()

# --- Flask Routes (Backend Endpoints) ---

@app.route('/')
def index():
    # Fetch all requests from the database, ordered by creation date
    requests = RoadClearingRequest.query.order_by(RoadClearingRequest.reported_at.desc()).all()
    return render_template('index.html', requests=requests)

@app.route('/add_request', methods=['GET', 'POST'])
def add_request():
    if request.method == 'POST':
        # Get data from the form
        reporter_name = request.form['reporter_name']
        contact_number = request.form.get('contact_number') # .get() allows it to be None if not provided
        barangay = request.form['barangay']
        street_address = request.form['street_address']
        description = request.form.get('description')
        status = request.form.get('status', 'Pending') # Default to 'Pending' if not provided

        # Generate a simple request_id (you might want a more robust generation in a real app)
        # For simplicity, let's use a timestamp and a random number
        timestamp_str = datetime.now().strftime('%Y%m%d%H%M%S')
        import random
        request_id = f"RC-{timestamp_str}-{random.randint(1000, 9999)}"

        # Create a new RoadClearingRequest object
        new_request = RoadClearingRequest(
            request_id=request_id,
            reporter_name=reporter_name,
            contact_number=contact_number,
            barangay=barangay,
            street_address=street_address,
            description=description,
            status=status
        )

        try:
            # Add the new request to the database session
            db.session.add(new_request)
            # Commit the transaction to save it to the database
            db.session.commit()
            return redirect(url_for('index')) # Redirect to the homepage
        except Exception as e:
            db.session.rollback() # Rollback in case of error
            print(f"Error adding request: {e}")
            return "There was an issue adding your request. Please try again.", 500
    else:
        # If it's a GET request, show the form
        return render_template('add_request.html')

# You can add more routes for updating, deleting, viewing single requests, etc.

# --- Run the Flask Application ---
if __name__ == '__main__':
    app.run(debug=True) # debug=True allows for auto-reloading and helpful error messages