import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime
from flask import Flask, request, jsonify

# Load the secret URL from the .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- DATABASE MODELS ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), default='Student') # 'Student' or 'Organizer'
    # Relationships
    events_organized = db.relationship('Event', backref='organizer', lazy=True)
    registrations = db.relationship('Registration', backref='student', lazy=True)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    registrations = db.relationship('Registration', backref='event', lazy=True)

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# --- ROUTES ---

# --- API ENDPOINTS ---

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    # Basic validation to prevent empty submissions
    if not data or not data.get('name') or not data.get('email'):
        return jsonify({"error": "Name and email are required"}), 400
        
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "User with this email already exists"}), 400

    new_user = User(
        name=data['name'],
        email=data['email'],
        role=data.get('role', 'Student') # Defaults to 'Student' if not provided
    )
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User created successfully", "user_id": new_user.id}), 201

@app.route('/api/events', methods=['POST'])
def create_event():
    data = request.get_json()
    
    # Convert string date from frontend to Python datetime object
    try:
        event_date = datetime.strptime(data['event_date'], '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD HH:MM:SS"}), 400

    new_event = Event(
        title=data['title'],
        description=data['description'],
        event_date=event_date,
        organizer_id=data['organizer_id']
    )
    db.session.add(new_event)
    db.session.commit()
    
    return jsonify({"message": "Event created successfully", "event_id": new_event.id}), 201

@app.route('/api/events', methods=['GET'])
def get_events():
    events = Event.query.order_by(Event.event_date.asc()).all()
    event_list = []
    for event in events:
        event_list.append({
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "event_date": event.event_date.strftime('%Y-%m-%d %H:%M:%S'),
            "organizer_id": event.organizer_id
        })
    return jsonify(event_list), 200

if __name__ == '__main__':
    app.run(debug=True)