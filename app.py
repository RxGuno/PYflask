from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import random
import requests

app = Flask(__name__)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
os.makedirs(app.instance_path, exist_ok=True)
db = SQLAlchemy(app)

# Database model
class RoadClearingRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.String(50), unique=True, nullable=False)
    reporter_name = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(20), nullable=True)
    barangay = db.Column(db.String(100), nullable=False)
    street_address = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='Pending')
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f"<Request {self.request_id} - {self.reporter_name} - {self.status}>"

with app.app_context():
    db.create_all()

# Geocoding function
def geocode_address(address):
    try:
        url = 'https://nominatim.openstreetmap.org/search'
        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }
        headers = {
            'User-Agent': 'Cainta-RoadClearing-System'
        }
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None, None

# Routes
@app.route('/')
def index():
    requests_data = RoadClearingRequest.query.order_by(RoadClearingRequest.reported_at.desc()).all()
    return render_template('index.html', requests=requests_data)

@app.route('/add_request', methods=['GET', 'POST'])
def add_request():
    if request.method == 'POST':
        reporter_name = request.form['reporter_name']
        contact_number = request.form.get('contact_number')
        barangay = request.form['barangay']
        street_address = request.form['street_address']
        description = request.form.get('description')
        status = request.form.get('status', 'Pending')

        timestamp_str = datetime.now().strftime('%Y%m%d%H%M%S')
        request_id = f"RC-{timestamp_str}-{random.randint(1000, 9999)}"

        # Generate full address
        full_address = f"{street_address}, {barangay}, Cainta, Rizal, Philippines"
        lat, lon = geocode_address(full_address)
        print(f"Geocoding: {full_address} → {lat}, {lon}")

        new_request = RoadClearingRequest(
            request_id=request_id,
            reporter_name=reporter_name,
            contact_number=contact_number,
            barangay=barangay,
            street_address=street_address,
            description=description,
            status=status,
            latitude=lat,
            longitude=lon
        )

        try:
            db.session.add(new_request)
            db.session.commit()
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            print(f"Error adding request: {e}")
            return "There was an issue adding your request.", 500

    return render_template('add_request.html')

if __name__ == '__main__':
    app.run(debug=True)
