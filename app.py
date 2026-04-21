from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

load_dotenv()

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key-change-in-production')

db = SQLAlchemy(app)
jwt = JWTManager(app)

# --- DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True) # Added for JWT Login
    role = db.Column(db.String(20), default='Student') 
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


# --- AUTHENTICATION ROUTES ---

@app.route('/api/register', methods=['POST'])
def register_admin():
    data = request.get_json()
    if not data or not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Name, email, and password required"}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "User already exists"}), 400

    hashed_pw = generate_password_hash(data['password'])
    new_user = User(
        name=data['name'], 
        email=data['email'], 
        password_hash=hashed_pw, 
        role='Organizer'
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Admin created successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    
    # Verify user exists and password matches the hash
    if not user or not user.password_hash or not check_password_hash(user.password_hash, data.get('password')):
        return jsonify({"error": "Invalid email or password"}), 401
        
    # Generate the security token
    access_token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": access_token, "role": user.role}), 200


# --- EVENT ROUTES ---

@app.route('/api/events', methods=['GET'])
def get_events():
    events = Event.query.all()
    return jsonify([{
        'id': e.id,
        'title': e.title,
        'description': e.description,
        'event_date': e.event_date.isoformat(),
        'organizer_id': e.organizer_id
    } for e in events]), 200

@app.route('/api/events', methods=['POST'])
@jwt_required() # <-- THE GATEKEEPER: Rejects requests without a valid token
def create_event():
    data = request.get_json()
    current_user_id = get_jwt_identity() # Extracts the Admin ID from the token
    
    if not data or not data.get('title') or not data.get('event_date'):
        return jsonify({'error': 'Missing title or event_date'}), 400
        
    try:
        parsed_date = datetime.fromisoformat(data['event_date'].replace('Z', '+00:00'))
        
        new_event = Event(
            title=data['title'],
            description=data.get('description', 'No description provided.'),
            event_date=parsed_date,
            organizer_id=current_user_id 
        )
        
        db.session.add(new_event)
        db.session.commit()
        return jsonify({'message': 'Event created successfully', 'id': new_event.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)