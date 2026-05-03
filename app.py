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

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'cgcu-catalyst-secret-2026')

db = SQLAlchemy(app)
jwt = JWTManager(app)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,       # auto-reconnects if DB was sleeping
    'pool_recycle': 300,         # recycles connections every 5 min
}

# ════════════════════════════════════════
# DATABASE MODELS
# ════════════════════════════════════════

class User(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(100), nullable=False)
    email          = db.Column(db.String(120), unique=True, nullable=False)
    password_hash  = db.Column(db.String(256), nullable=True)
    branch         = db.Column(db.String(100), nullable=True)
    year           = db.Column(db.String(20), nullable=True)
    role           = db.Column(db.String(20), default='Student')
    registrations  = db.relationship('Registration', backref='student', lazy=True)

class Club(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), unique=True, nullable=False)
    description   = db.Column(db.Text, nullable=True)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    color1        = db.Column(db.String(10), default='#E1352F')
    color2        = db.Column(db.String(10), default='#FF7A4C')
    followers     = db.Column(db.Integer, default=0)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    events        = db.relationship('Event', backref='club', lazy=True)

class Event(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    title         = db.Column(db.String(200), nullable=False)
    description   = db.Column(db.Text, nullable=False)
    category      = db.Column(db.String(50), default='Workshop')
    event_date    = db.Column(db.DateTime, nullable=False)
    time_str      = db.Column(db.String(50), nullable=True)
    venue         = db.Column(db.String(200), default='CGCU Mohali')
    max_slots     = db.Column(db.Integer, default=100)
    price         = db.Column(db.Integer, default=0)
    team_size     = db.Column(db.String(50), default='Individual')
    status        = db.Column(db.String(20), default='upcoming')
    club_id       = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=True)
    organizer_id  = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    registrations = db.relationship('Registration', backref='event', lazy=True)

class Registration(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id  = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    team_name = db.Column(db.String(100), nullable=True)
    phone     = db.Column(db.String(20), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# ════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════

def club_to_dict(c):
    return {
        'id': c.id, 'name': c.name, 'description': c.description,
        'email': c.email, 'color1': c.color1, 'color2': c.color2,
        'followers': c.followers, 'eventsCount': len(c.events),
        'created_at': c.created_at.isoformat()
    }

def event_to_dict(e):
    club_name = e.club.name if e.club else 'CGCU'
    return {
        'id': e.id, 'title': e.title, 'description': e.description,
        'category': e.category, 'event_date': e.event_date.isoformat(),
        'time_str': e.time_str, 'venue': e.venue,
        'max_slots': e.max_slots, 'registered_count': len(e.registrations),
        'price': e.price, 'team_size': e.team_size, 'status': e.status,
        'club_id': e.club_id, 'club_name': club_name,
        'color1': e.club.color1 if e.club else '#E1352F',
        'color2': e.club.color2 if e.club else '#FF7A4C',
    }


# ════════════════════════════════════════
# STUDENT AUTH
# ════════════════════════════════════════

@app.route('/api/register', methods=['POST'])
def register_student():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    user = User(
        name=data.get('name', ''),
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        branch=data.get('branch', ''),
        year=data.get('year', ''),
        role='Student'
    )
    db.session.add(user)
    db.session.commit()
    token = create_access_token(identity=f'student:{user.id}')
    return jsonify({'access_token': token, 'role': 'Student', 'name': user.name}), 201

@app.route('/api/login', methods=['POST'])
def login_student():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    if not user or not user.password_hash or not check_password_hash(user.password_hash, data.get('password', '')):
        return jsonify({'error': 'Invalid email or password'}), 401
    token = create_access_token(identity=f'student:{user.id}')
    return jsonify({'access_token': token, 'role': user.role, 'name': user.name}), 200


# ════════════════════════════════════════
# CLUB AUTH
# ════════════════════════════════════════

@app.route('/api/clubs/register', methods=['POST'])
def register_club():
    data = request.get_json()
    if not all(data.get(k) for k in ['name', 'email', 'password']):
        return jsonify({'error': 'name, email, password required'}), 400
    if Club.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Club email already registered'}), 400
    if Club.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Club name already taken'}), 400
    club = Club(
        name=data['name'],
        email=data['email'].lower(),
        password_hash=generate_password_hash(data['password']),
        description=data.get('description', ''),
        color1=data.get('color1', '#E1352F'),
        color2=data.get('color2', '#FF7A4C'),
    )
    db.session.add(club)
    db.session.commit()
    return jsonify({'message': f"Club '{club.name}' registered!", 'id': club.id}), 201

@app.route('/api/clubs/login', methods=['POST'])
def login_club():
    data = request.get_json()
    club = Club.query.filter_by(email=data.get('email', '').lower()).first()
    if not club or not check_password_hash(club.password_hash, data.get('password', '')):
        return jsonify({'error': 'Invalid club email or password'}), 401
    token = create_access_token(identity=f'club:{club.id}')
    return jsonify({
        'access_token': token,
        'club_id':   club.id,
        'club_name': club.name,
        'color1':    club.color1,
        'color2':    club.color2,
    }), 200


# ════════════════════════════════════════
# PUBLIC CLUB ROUTES
# ════════════════════════════════════════

@app.route('/api/clubs', methods=['GET'])
def get_clubs():
    clubs = Club.query.all()
    return jsonify([club_to_dict(c) for c in clubs]), 200

@app.route('/api/clubs/<int:club_id>', methods=['GET'])
def get_club(club_id):
    club = Club.query.get_or_404(club_id)
    data = club_to_dict(club)
    data['events'] = [event_to_dict(e) for e in club.events if e.status != 'completed']
    return jsonify(data), 200


# ════════════════════════════════════════
# PUBLIC EVENT ROUTES
# ════════════════════════════════════════

@app.route('/api/events', methods=['GET'])
def get_events():
    category = request.args.get('category')
    status   = request.args.get('status', 'upcoming')
    query    = Event.query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)
    events = query.order_by(Event.event_date).all()
    return jsonify([event_to_dict(e) for e in events]), 200

@app.route('/api/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    event = Event.query.get_or_404(event_id)
    return jsonify(event_to_dict(event)), 200

@app.route('/api/events/<int:event_id>/register', methods=['POST'])
@jwt_required()
def register_for_event(event_id):
    identity = get_jwt_identity()
    if not identity.startswith('student:'):
        return jsonify({'error': 'Only students can register'}), 403
    user_id = int(identity.split(':')[1])
    event = Event.query.get_or_404(event_id)
    if len(event.registrations) >= event.max_slots:
        return jsonify({'error': 'Event is fully booked'}), 400
    if Registration.query.filter_by(user_id=user_id, event_id=event_id).first():
        return jsonify({'error': 'Already registered'}), 400
    data = request.get_json() or {}
    reg = Registration(user_id=user_id, event_id=event_id,
                       team_name=data.get('team_name'), phone=data.get('phone'))
    db.session.add(reg)
    db.session.commit()
    return jsonify({'message': 'Registered successfully!'}), 201


# ════════════════════════════════════════
# CLUB ADMIN ROUTES
# ════════════════════════════════════════

def get_club_from_token():
    identity = get_jwt_identity()
    if identity and identity.startswith('club:'):
        return Club.query.get(int(identity.split(':')[1]))
    return None

@app.route('/api/admin/events', methods=['POST'])
@jwt_required()
def admin_create_event():
    club = get_club_from_token()
    if not club:
        return jsonify({'error': 'Club admin access required'}), 403
    data = request.get_json()
    if not data or not data.get('title') or not data.get('event_date'):
        return jsonify({'error': 'title and event_date are required'}), 400
    try:
        parsed_date = datetime.fromisoformat(data['event_date'].replace('Z', '+00:00'))
        event = Event(
            title=data['title'],
            description=data.get('description', ''),
            category=data.get('category', 'Workshop'),
            event_date=parsed_date,
            time_str=data.get('time_str', ''),
            venue=data.get('venue', 'CGCU Mohali'),
            max_slots=int(data.get('max_slots', 100)),
            price=int(data.get('price', 0)),
            team_size=data.get('team_size', 'Individual'),
            status='upcoming',
            club_id=club.id,
        )
        db.session.add(event)
        db.session.commit()
        return jsonify({'message': 'Event created!', 'id': event.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/events/<int:event_id>', methods=['PUT'])
@jwt_required()
def admin_update_event(event_id):
    club = get_club_from_token()
    if not club:
        return jsonify({'error': 'Club admin access required'}), 403
    event = Event.query.get_or_404(event_id)
    if event.club_id != club.id:
        return jsonify({'error': 'You can only edit your own events'}), 403
    data = request.get_json()
    for field in ['title', 'description', 'category', 'time_str', 'venue', 'team_size', 'status']:
        if field in data:
            setattr(event, field, data[field])
    if 'max_slots' in data:
        event.max_slots = int(data['max_slots'])
    if 'price' in data:
        event.price = int(data['price'])
    if 'event_date' in data:
        event.event_date = datetime.fromisoformat(data['event_date'].replace('Z', '+00:00'))
    db.session.commit()
    return jsonify({'message': 'Event updated!'}), 200

@app.route('/api/admin/events/<int:event_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_event(event_id):
    club = get_club_from_token()
    if not club:
        return jsonify({'error': 'Club admin access required'}), 403
    event = Event.query.get_or_404(event_id)
    if event.club_id != club.id:
        return jsonify({'error': 'You can only delete your own events'}), 403
    Registration.query.filter_by(event_id=event_id).delete()
    db.session.delete(event)
    db.session.commit()
    return jsonify({'message': 'Event deleted'}), 200

@app.route('/api/admin/events', methods=['GET'])
@jwt_required()
def admin_get_my_events():
    club = get_club_from_token()
    if not club:
        return jsonify({'error': 'Club admin access required'}), 403
    events = Event.query.filter_by(club_id=club.id).order_by(Event.event_date).all()
    return jsonify([event_to_dict(e) for e in events]), 200

@app.route('/api/admin/events/<int:event_id>/registrations', methods=['GET'])
@jwt_required()
def admin_get_registrations(event_id):
    club = get_club_from_token()
    if not club:
        return jsonify({'error': 'Club admin access required'}), 403
    event = Event.query.get_or_404(event_id)
    if event.club_id != club.id:
        return jsonify({'error': 'Access denied'}), 403
    regs = Registration.query.filter_by(event_id=event_id).all()
    result = []
    for r in regs:
        user = User.query.get(r.user_id)
        result.append({
            'id': r.id,
            'name':      user.name   if user else 'Unknown',
            'email':     user.email  if user else '',
            'branch':    user.branch if user else '',
            'year':      user.year   if user else '',
            'team_name': r.team_name,
            'phone':     r.phone,
            'registered_at': r.timestamp.isoformat()
        })
    return jsonify(result), 200


# ════════════════════════════════════════
# SETUP + MIGRATE
# ════════════════════════════════════════

def seed_clubs():
    clubs_data = [
        {'name': 'DevSoc',    'email': 'devsoc@cgcuniversity.in',   'password': 'devsoc123',   'description': 'Developer Society of CGCU',             'color1': '#E1352F', 'color2': '#FF7A4C'},
        {'name': 'IEEE Club', 'email': 'ieee@cgcuniversity.in',      'password': 'ieee123',     'description': 'Institute of Electrical & Electronics', 'color1': '#1e3a8a', 'color2': '#3b82f6'},
        {'name': 'E-Cell',    'email': 'ecell@cgcuniversity.in',     'password': 'ecell123',    'description': 'Entrepreneurship Cell CGCU',            'color1': '#064e3b', 'color2': '#10b981'},
        {'name': 'AI Club',   'email': 'aiclub@cgcuniversity.in',    'password': 'aiclub123',   'description': 'Artificial Intelligence & ML Club',     'color1': '#1e1b4b', 'color2': '#6d28d9'},
        {'name': 'GDSC',      'email': 'gdsc@cgcuniversity.in',      'password': 'gdsc123',     'description': 'Google Developer Student Club',         'color1': '#1e3a8a', 'color2': '#4285F4'},
        {'name': 'Code Club', 'email': 'codeclub@cgcuniversity.in',  'password': 'code123',     'description': 'Competitive Programming Club',          'color1': '#581c87', 'color2': '#c026d3'},
        {'name': 'Robotics',  'email': 'robotics@cgcuniversity.in',  'password': 'robotics123', 'description': 'Robotics & IoT Club',                   'color1': '#064e3b', 'color2': '#0d9488'},
        {'name': 'CyberSec',  'email': 'cybersec@cgcuniversity.in',  'password': 'cybersec123', 'description': 'Cyber Security Club',                   'color1': '#1a0a0a', 'color2': '#dc2626'},
    ]
    added = 0
    for c in clubs_data:
        if not Club.query.filter_by(email=c['email']).first():
            club = Club(
                name=c['name'], email=c['email'],
                password_hash=generate_password_hash(c['password']),
                description=c['description'],
                color1=c['color1'], color2=c['color2'],
            )
            db.session.add(club)
            added += 1
    if added:
        db.session.commit()
        print(f'✅ Seeded {added} clubs into database')
    else:
        print('ℹ️  All clubs already exist')

@app.route('/api/setup', methods=['POST'])
def setup():
    with app.app_context():
        db.create_all()
        seed_clubs()
    return jsonify({'message': 'Database ready and clubs seeded!'}), 200

@app.route('/api/migrate', methods=['POST'])
def migrate():
    """
    Adds missing columns to existing tables.
    Safe to run multiple times — IF NOT EXISTS prevents errors.
    """
    from sqlalchemy import text
    sql = """
    ALTER TABLE "user" ADD COLUMN IF NOT EXISTS branch VARCHAR(100);
    ALTER TABLE "user" ADD COLUMN IF NOT EXISTS year VARCHAR(20);
    ALTER TABLE event ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'Workshop';
    ALTER TABLE event ADD COLUMN IF NOT EXISTS time_str VARCHAR(50);
    ALTER TABLE event ADD COLUMN IF NOT EXISTS venue VARCHAR(200) DEFAULT 'CGCU Mohali';
    ALTER TABLE event ADD COLUMN IF NOT EXISTS max_slots INTEGER DEFAULT 100;
    ALTER TABLE event ADD COLUMN IF NOT EXISTS price INTEGER DEFAULT 0;
    ALTER TABLE event ADD COLUMN IF NOT EXISTS team_size VARCHAR(50) DEFAULT 'Individual';
    ALTER TABLE event ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'upcoming';
    ALTER TABLE event ADD COLUMN IF NOT EXISTS club_id INTEGER;
    ALTER TABLE event ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
    """
    try:
        with db.engine.begin() as conn:
            conn.execute(text(sql))
        return jsonify({'message': 'Migration complete!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/api/migrate2', methods=['POST'])
def migrate2():
    from sqlalchemy import text
    sql = """
    ALTER TABLE event ALTER COLUMN organizer_id DROP NOT NULL;
    """
    try:
        with db.engine.begin() as conn:
            conn.execute(text(sql))
        return jsonify({'message': 'migrate2 complete!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/migrate3', methods=['POST'])
def migrate3():
    from sqlalchemy import text
    sql = """
    ALTER TABLE registration ADD COLUMN IF NOT EXISTS team_name VARCHAR(100);
    ALTER TABLE registration ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
    ALTER TABLE event ALTER COLUMN organizer_id DROP NOT NULL;
    """
    try:
        with db.engine.begin() as conn:
            conn.execute(text(sql))
        return jsonify({'message': 'migrate3 complete!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500        


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)