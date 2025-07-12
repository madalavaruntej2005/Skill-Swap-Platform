from flask import Flask
from flask_cors import CORS

# 1. First create the Flask application
app = Flask(__name__)

# 2. Then configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],  # Your frontend URL
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Your routes go here
@app.route('/')
def home():
    return "Welcome to SkillSwap!"

# Database and other configurations...

if __name__ == '__main__':
    app.run(debug=True)
    import secrets
app.secret_key = secrets.token_hex(32)  # For session security

from flask_jwt_extended import JWTManager, create_access_token
app.config['JWT_SECRET_KEY'] = secrets.token_hex(32)
jwt = JWTManager(app)

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)

if __name__ == '__main__':
    app.run(port=5001)  # Use a different port

    # ... after creating your Flask app ...

# JWT Configuration
app.config['JWT_SECRET_KEY'] = 'your-secret-key-here'  # Change this to a random secret key
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
jwt = JWTManager(app)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (data['email'],)).fetchone()
    conn.close()
    
    if not user or not check_password_hash(user['password_hash'], data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Create JWT token
    access_token = create_access_token(identity={
        'id': user['id'],
        'email': user['email'],
        'is_admin': user['is_admin']
    })
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'is_admin': user['is_admin']
        }
    }), 200

# Database setup
DATABASE = 'skill_swap.db'

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            location TEXT,
            profile_photo TEXT,
            skills_offered TEXT,
            skills_wanted TEXT,
            availability TEXT,
            is_public BOOLEAN DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Swap requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS swap_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,
            my_skill TEXT NOT NULL,
            wanted_skill TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            rating INTEGER,
            feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_user_id) REFERENCES users (id),
            FOREIGN KEY (to_user_id) REFERENCES users (id)
        )
    ''')
    
    # Create default admin user
    cursor.execute('''
        INSERT OR IGNORE INTO users (name, email, password_hash, is_admin)
        VALUES ('Admin', 'admin@skillswap.com', ?, 1)
    ''', (generate_password_hash('admin123'),))
    
    conn.commit()
    conn.close()

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    """Decorator to require login for certain endpoints"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        
        conn = get_db()
        user = conn.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        
        if not user or not user['is_admin']:
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Authentication endpoints
@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Name, email, and password are required'}), 400
    
    conn = get_db()
    
    # Check if user already exists
    existing_user = conn.execute('SELECT id FROM users WHERE email = ?', (data['email'],)).fetchone()
    if existing_user:
        conn.close()
        return jsonify({'error': 'User already exists'}), 409
    
    # Create new user
    password_hash = generate_password_hash(data['password'])
    cursor = conn.execute('''
        INSERT INTO users (name, email, password_hash, location, profile_photo, 
                          skills_offered, skills_wanted, availability, is_public)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['name'],
        data['email'],
        password_hash,
        data.get('location', ''),
        data.get('profile_photo', ''),
        ','.join(data.get('skills_offered', [])),
        ','.join(data.get('skills_wanted', [])),
        data.get('availability', 'weekends'),
        data.get('is_public', True)
    ))
    
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    session['user_id'] = user_id
    return jsonify({'message': 'User registered successfully', 'user_id': user_id}), 201

@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (data['email'],)).fetchone()
    conn.close()
    
    if not user or not check_password_hash(user['password_hash'], data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    session['user_id'] = user['id']
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'is_admin': user['is_admin']
        }
    }), 200

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    """Logout user"""
    session.pop('user_id', None)
    return jsonify({'message': 'Logout successful'}), 200

# User profile endpoints
@app.route('/api/profile', methods=['GET'])
@login_required
def get_profile():
    """Get current user's profile"""
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'location': user['location'],
        'profile_photo': user['profile_photo'],
        'skills_offered': user['skills_offered'].split(',') if user['skills_offered'] else [],
        'skills_wanted': user['skills_wanted'].split(',') if user['skills_wanted'] else [],
        'availability': user['availability'],
        'is_public': user['is_public'],
        'created_at': user['created_at']
    }), 200

@app.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update current user's profile"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    conn = get_db()
    conn.execute('''
        UPDATE users SET 
            name = ?, location = ?, profile_photo = ?, 
            skills_offered = ?, skills_wanted = ?, 
            availability = ?, is_public = ?
        WHERE id = ?
    ''', (
        data.get('name'),
        data.get('location', ''),
        data.get('profile_photo', ''),
        ','.join(data.get('skills_offered', [])),
        ','.join(data.get('skills_wanted', [])),
        data.get('availability', 'weekends'),
        data.get('is_public', True),
        session['user_id']
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Profile updated successfully'}), 200

# User browsing endpoints
@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    """Get all public users except current user"""
    search_skill = request.args.get('skill', '')
    
    conn = get_db()
    query = '''
        SELECT id, name, location, profile_photo, skills_offered, skills_wanted, availability
        FROM users 
        WHERE is_public = 1 AND id != ?
    '''
    params = [session['user_id']]
    
    if search_skill:
        query += ' AND (skills_offered LIKE ? OR skills_wanted LIKE ?)'
        params.extend([f'%{search_skill}%', f'%{search_skill}%'])
    
    users = conn.execute(query, params).fetchall()
    conn.close()
    
    users_list = []
    for user in users:
        users_list.append({
            'id': user['id'],
            'name': user['name'],
            'location': user['location'],
            'profile_photo': user['profile_photo'],
            'skills_offered': user['skills_offered'].split(',') if user['skills_offered'] else [],
            'skills_wanted': user['skills_wanted'].split(',') if user['skills_wanted'] else [],
            'availability': user['availability']
        })
    
    return jsonify(users_list), 200

# Swap request endpoints
@app.route('/api/swap-requests', methods=['POST'])
@login_required
def create_swap_request():
    """Create a new swap request"""
    data = request.get_json()
    
    if not data or not data.get('to_user_id') or not data.get('my_skill') or not data.get('wanted_skill'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if request already exists
    conn = get_db()
    existing = conn.execute('''
        SELECT id FROM swap_requests 
        WHERE from_user_id = ? AND to_user_id = ? AND status = 'pending'
    ''', (session['user_id'], data['to_user_id'])).fetchone()
    
    if existing:
        conn.close()
        return jsonify({'error': 'Pending request already exists'}), 409
    
    # Create new request
    cursor = conn.execute('''
        INSERT INTO swap_requests (from_user_id, to_user_id, my_skill, wanted_skill)
        VALUES (?, ?, ?, ?)
    ''', (session['user_id'], data['to_user_id'], data['my_skill'], data['wanted_skill']))
    
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Swap request created', 'request_id': request_id}), 201

@app.route('/api/swap-requests', methods=['GET'])
@login_required
def get_swap_requests():
    """Get swap requests for current user"""
    request_type = request.args.get('type', 'all')  # 'sent', 'received', 'all'
    
    conn = get_db()
    
    if request_type == 'sent':
        query = '''
            SELECT sr.*, u.name as to_user_name
            FROM swap_requests sr
            JOIN users u ON sr.to_user_id = u.id
            WHERE sr.from_user_id = ?
            ORDER BY sr.created_at DESC
        '''
        params = [session['user_id']]
    elif request_type == 'received':
        query = '''
            SELECT sr.*, u.name as from_user_name
            FROM swap_requests sr
            JOIN users u ON sr.from_user_id = u.id
            WHERE sr.to_user_id = ?
            ORDER BY sr.created_at DESC
        '''
        params = [session['user_id']]
    else:  # all
        query = '''
            SELECT sr.*, 
                   u1.name as from_user_name,
                   u2.name as to_user_name
            FROM swap_requests sr
            JOIN users u1 ON sr.from_user_id = u1.id
            JOIN users u2 ON sr.to_user_id = u2.id
            WHERE sr.from_user_id = ? OR sr.to_user_id = ?
            ORDER BY sr.created_at DESC
        '''
        params = [session['user_id'], session['user_id']]
    
    requests = conn.execute(query, params).fetchall()
    conn.close()
    
    requests_list = []
    for req in requests:
        requests_list.append({
            'id': req['id'],
            'from_user_id': req['from_user_id'],
            'to_user_id': req['to_user_id'],
            'from_user_name': req.get('from_user_name'),
            'to_user_name': req.get('to_user_name'),
            'my_skill': req['my_skill'],
            'wanted_skill': req['wanted_skill'],
            'status': req['status'],
            'rating': req['rating'],
            'feedback': req['feedback'],
            'created_at': req['created_at']
        })
    
    return jsonify(requests_list), 200

@app.route('/api/swap-requests/<int:request_id>', methods=['PUT'])
@login_required
def update_swap_request(request_id):
    """Update swap request status or rating"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    conn = get_db()
    
    # Check if user has permission to update this request
    swap_request = conn.execute('''
        SELECT * FROM swap_requests WHERE id = ?
    ''', (request_id,)).fetchone()
    
    if not swap_request:
        conn.close()
        return jsonify({'error': 'Request not found'}), 404
    
    # For status updates, only the recipient can update
    if 'status' in data:
        if swap_request['to_user_id'] != session['user_id']:
            conn.close()
            return jsonify({'error': 'Permission denied'}), 403
        
        conn.execute('''
            UPDATE swap_requests SET status = ? WHERE id = ?
        ''', (data['status'], request_id))
    
    # For rating updates, either user can rate
    if 'rating' in data or 'feedback' in data:
        if swap_request['from_user_id'] != session['user_id'] and swap_request['to_user_id'] != session['user_id']:
            conn.close()
            return jsonify({'error': 'Permission denied'}), 403
        
        update_fields = []
        params = []
        
        if 'rating' in data:
            update_fields.append('rating = ?')
            params.append(data['rating'])
        
        if 'feedback' in data:
            update_fields.append('feedback = ?')
            params.append(data['feedback'])
        
        params.append(request_id)
        
        conn.execute(f'''
            UPDATE swap_requests SET {', '.join(update_fields)} WHERE id = ?
        ''', params)
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Request updated successfully'}), 200

@app.route('/api/swap-requests/<int:request_id>', methods=['DELETE'])
@login_required
def delete_swap_request(request_id):
    """Delete a swap request"""
    conn = get_db()
    
    # Check if user has permission to delete this request
    swap_request = conn.execute('''
        SELECT * FROM swap_requests WHERE id = ?
    ''', (request_id,)).fetchone()
    
    if not swap_request:
        conn.close()
        return jsonify({'error': 'Request not found'}), 404
    
    # Only the sender can delete their own request
    if swap_request['from_user_id'] != session['user_id']:
        conn.close()
        return jsonify({'error': 'Permission denied'}), 403
    
    conn.execute('DELETE FROM swap_requests WHERE id = ?', (request_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Request deleted successfully'}), 200

# Admin endpoints
@app.route('/api/admin/stats', methods=['GET'])
@admin_required
def get_admin_stats():
    """Get admin dashboard statistics"""
    conn = get_db()
    
    # Get various statistics
    total_users = conn.execute('SELECT COUNT(*) as count FROM users WHERE is_admin = 0').fetchone()['count']
    total_swaps = conn.execute('SELECT COUNT(*) as count FROM swap_requests').fetchone()['count']
    pending_swaps = conn.execute('SELECT COUNT(*) as count FROM swap_requests WHERE status = "pending"').fetchone()['count']
    active_users = conn.execute('SELECT COUNT(*) as count FROM users WHERE is_public = 1 AND is_admin = 0').fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'total_users': total_users,
        'total_swaps': total_swaps,
        'pending_swaps': pending_swaps,
        'active_users': active_users
    }), 200

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def get_admin_users():
    """Get all users for admin management"""
    conn = get_db()
    users = conn.execute('''
        SELECT id, name, email, location, skills_offered, skills_wanted, 
               availability, is_public, created_at
        FROM users 
        WHERE is_admin = 0
        ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    
    users_list = []
    for user in users:
        users_list.append({
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'location': user['location'],
            'skills_offered': user['skills_offered'].split(',') if user['skills_offered'] else [],
            'skills_wanted': user['skills_wanted'].split(',') if user['skills_wanted'] else [],
            'availability': user['availability'],
            'is_public': user['is_public'],
            'created_at': user['created_at']
        })
    
    return jsonify(users_list), 200

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user_admin(user_id):
    """Update user as admin"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    conn = get_db()
    
    # Check if user exists
    user = conn.execute('SELECT id FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    # Update user
    if 'is_public' in data:
        conn.execute('UPDATE users SET is_public = ? WHERE id = ?', (data['is_public'], user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'User updated successfully'}), 200

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user_admin(user_id):
    """Delete user as admin"""
    conn = get_db()
    
    # Check if user exists
    user = conn.execute('SELECT id FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    # Delete user and their swap requests
    conn.execute('DELETE FROM swap_requests WHERE from_user_id = ? OR to_user_id = ?', (user_id, user_id))
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'User deleted successfully'}), 200

@app.route('/api/admin/swap-requests', methods=['GET'])
@admin_required
def get_admin_swap_requests():
    """Get all swap requests for admin management"""
    conn = get_db()
    requests = conn.execute('''
        SELECT sr.*, 
               u1.name as from_user_name,
               u2.name as to_user_name
        FROM swap_requests sr
        JOIN users u1 ON sr.from_user_id = u1.id
        JOIN users u2 ON sr.to_user_id = u2.id
        ORDER BY sr.created_at DESC
    ''').fetchall()
    conn.close()
    
    requests_list = []
    for req in requests:
        requests_list.append({
            'id': req['id'],
            'from_user_id': req['from_user_id'],
            'to_user_id': req['to_user_id'],
            'from_user_name': req['from_user_name'],
            'to_user_name': req['to_user_name'],
            'my_skill': req['my_skill'],
            'wanted_skill': req['wanted_skill'],
            'status': req['status'],
            'rating': req['rating'],
            'feedback': req['feedback'],
            'created_at': req['created_at']
        })
    
    return jsonify(requests_list), 200

@app.route('/api/admin/swap-requests/<int:request_id>', methods=['DELETE'])
@admin_required
def delete_swap_request_admin(request_id):
    """Delete swap request as admin"""
    conn = get_db()
    
    # Check if request exists
    request_exists = conn.execute('SELECT id FROM swap_requests WHERE id = ?', (request_id,)).fetchone()
    if not request_exists:
        conn.close()
        return jsonify({'error': 'Request not found'}), 404
    
    conn.execute('DELETE FROM swap_requests WHERE id = ?', (request_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Request deleted successfully'}), 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)