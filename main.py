# LiftLink Carpool - Enhanced Flask Web Application with Full Ride Sharing
# Spyder Compatible - Xavier's Institute of Engineering - Sustainable Commute Hub
# Version 8.2 - FIXED: Users can now see and book rides from other users

import os
import sys
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename
from functools import wraps
import hashlib
import secrets
from datetime import datetime, date

# Try to import PIL for image processing, fallback if not available
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL not available - images will be saved without resizing")

# Ensure we're in the right directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Debug info
print("=" * 60)
print(" LIFTLINK CARPOOL - ENHANCED VERSION 8.2")
print("=" * 60)
print(f"Current directory: {os.getcwd()}")
print(f"Templates exist: {os.path.exists('templates')}")
print(f"Static folder exists: {os.path.exists('static')}")

if os.path.exists('templates'):
    try:
        print(f"Template files: {os.listdir('templates')}")
    except PermissionError:
        print("Permission denied accessing templates folder")

print("=" * 60)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'xie-liftlink-secretkey-2025-enhanced-v8'

# Profile Picture Configuration
UPLOAD_FOLDER = 'static/uploads/profilepics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('static/images', exist_ok=True)
os.makedirs('data', exist_ok=True)  # Create data directory for persistent storage

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# File paths for persistent storage
USERS_DB_FILE = 'data/users_db.json'
RIDES_DB_FILE = 'data/rides_db.json'

# Profile Picture Helper Functions
def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_picture(form_picture, current_user_email):
    """Save and optionally resize profile picture"""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = f"{current_user_email.replace('@', '_').replace('.', '_')}_{random_hex}{f_ext}"
    picture_path = os.path.join(app.root_path, 'static', 'uploads', 'profilepics', picture_fn)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    
    if PIL_AVAILABLE:
        output_size = (300, 300)
        try:
            img = Image.open(form_picture)
            # Convert to RGB if it's RGBA for PNG with transparency
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            img.thumbnail(output_size, Image.Resampling.LANCZOS)
            img.save(picture_path, quality=90, optimize=True)
            print(f"✓ Profile picture saved and resized: {picture_fn}")
        except Exception as e:
            print(f"✗ PIL resize failed, saving directly: {e}")
            form_picture.save(picture_path)
    else:
        # If PIL is not available, just save the file directly
        form_picture.save(picture_path)
        print(f"✓ Profile picture saved: {picture_fn}")
    
    # Verify file was saved
    if os.path.exists(picture_path):
        file_size = os.path.getsize(picture_path)
        print(f"✓ File saved successfully: {picture_path} ({file_size} bytes)")
    else:
        print(f"✗ File NOT saved: {picture_path}")
    
    return picture_fn

# Persistent Storage Functions
def load_users_db():
    """Load users database from JSON file"""
    try:
        if os.path.exists(USERS_DB_FILE):
            with open(USERS_DB_FILE, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
                print(f"✓ Loaded {len(users_data)} users from database")
                return users_data
        else:
            print("Creating new users database...")
            return get_default_users()
    except Exception as e:
        print(f"✗ Error loading users database: {e}")
        return get_default_users()

def save_users_db(users_data):
    """Save users database to JSON file"""
    try:
        with open(USERS_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved {len(users_data)} users to database")
        return True
    except Exception as e:
        print(f"✗ Error saving users database: {e}")
        return False

def load_rides_db():
    """Load rides database from JSON file"""
    try:
        if os.path.exists(RIDES_DB_FILE):
            with open(RIDES_DB_FILE, 'r', encoding='utf-8') as f:
                rides_data = json.load(f)
                print(f"✓ Loaded {len(rides_data)} rides from database")
                return rides_data
        else:
            print("Creating new rides database...")
            return get_default_rides()
    except Exception as e:
        print(f"✗ Error loading rides database: {e}")
        return get_default_rides()

def save_rides_db(rides_data):
    """Save rides database to JSON file"""
    try:
        with open(RIDES_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(rides_data, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved {len(rides_data)} rides to database")
        return True
    except Exception as e:
        print(f"✗ Error saving rides database: {e}")
        return False

def get_default_users():
    """Get default users for first-time setup"""
    return {
        # Test Student Account
        'test@student.xavier.ac.in': {
            'name': 'Durvesh Bedre',
            'email': 'test@student.xavier.ac.in',
            'password': hashlib.sha256('password123'.encode()).hexdigest(),
            'phone': '7700090035',
            'student_id': '2023032002',
            'department': 'Electronics & Telecommunication Engg',
            'year': 4,
            'gender': 'Male',
            'about': 'Final year ETC student interested in sustainable transportation.',
            'profile_pic': None,
            'verified': True,
            'user_type': 'student'
        },
        # Test Staff Account
        'john.doe@xavier.ac.in': {
            'name': 'Dr. John Doe',
            'email': 'john.doe@xavier.ac.in',
            'password': hashlib.sha256('staff123'.encode()).hexdigest(),
            'phone': '9876543210',
            'employee_id': 'XIE001',
            'department': 'Computer Science Engg',
            'designation': 'Assistant Professor',
            'about': 'Assistant Professor in Computer Engineering Department.',
            'profile_pic': None,
            'verified': True,
            'user_type': 'staff',
            'car_model': 'Honda City',
            'max_passengers': 3
        },
        # Admin Account
        'admin@student.xavier.ac.in': {
            'name': 'Admin User',
            'email': 'admin@student.xavier.ac.in',
            'password': hashlib.sha256('admin123'.encode()).hexdigest(),
            'phone': '9876543210',
            'student_id': '2023000001',
            'department': 'Computer Science Engg',
            'year': 4,
            'gender': 'Male',
            'about': 'System Administrator',
            'profile_pic': None,
            'verified': True,
            'user_type': 'student'
        },
        # Additional Staff Account
        'priya.patil@xavier.ac.in': {
            'name': 'Dr. Priya Patil',
            'email': 'priya.patil@xavier.ac.in',
            'password': hashlib.sha256('staff123'.encode()).hexdigest(),
            'phone': '9876543211',
            'employee_id': 'XIE002',
            'department': 'Electronics & Telecommunication Engg',
            'designation': 'Associate Professor',
            'about': 'Associate Professor in Electronics & Telecom Department.',
            'profile_pic': None,
            'verified': True,
            'user_type': 'staff',
            'car_model': 'Maruti Swift',
            'max_passengers': 3
        }
    }

def get_default_rides():
    """Get default rides for first-time setup"""
    today = datetime.now().strftime('%Y-%m-%d')
    return [
        {
            'id': 1,
            'driver_name': 'Rohit Sharma',
            'driver_email': '2023032001.rohit@student.xavier.ac.in',
            'from_location': 'Vashi Station',
            'to_location': 'Xavier Institute of Engineering',
            'departure_time': '08:00',
            'date': today,
            'available_seats': 3,
            'total_seats': 4,
            'car_model': 'Honda City',
            'price_per_seat': 25,
            'department': 'Computer Engineering',
            'year': '3rd Year',
            'rating': 4.5,
            'phone': '9876543210',
            'additional_info': 'Pickup near main gate, AC available'
        },
        {
            'id': 2,
            'driver_name': 'Dr. Priya Patil',
            'driver_email': 'priya.patil@xavier.ac.in',
            'from_location': 'Nerul Station',
            'to_location': 'Xavier Institute of Engineering',
            'departure_time': '08:15',
            'date': today,
            'available_seats': 2,
            'total_seats': 3,
            'car_model': 'Maruti Swift',
            'price_per_seat': 20,
            'department': 'Electronics & Telecom',
            'designation': 'Associate Professor',
            'rating': 4.8,
            'phone': '9876543211',
            'additional_info': 'Regular route, music system available'
        }
    ]

# Initialize persistent databases
users_db = load_users_db()
sample_rides = load_rides_db()

class User:
    """Enhanced User class with staff support"""
    def __init__(self, email):
        self.email = email
        self.data = users_db.get(email, {})
        if not self.data:
            print(f"User not found in database: {email}")

    @property
    def name(self):
        return self.data.get('name', 'User')

    @property
    def phone(self):
        return self.data.get('phone', '')

    @property
    def student_id(self):
        return self.data.get('student_id', '')

    @property
    def employee_id(self):
        return self.data.get('employee_id', '')

    @property
    def department(self):
        return self.data.get('department', '')

    @property
    def year(self):
        return self.data.get('year', 1)

    @property
    def designation(self):
        return self.data.get('designation', '')

    @property
    def gender(self):
        return self.data.get('gender', '')

    @property
    def about(self):
        return self.data.get('about', '')

    @property
    def user_type(self):
        return self.data.get('user_type', 'student')

    @property
    def car_model(self):
        return self.data.get('car_model', '')

    @property
    def max_passengers(self):
        return self.data.get('max_passengers', 0)

    @property
    def profile_pic(self):
        pic = self.data.get('profile_pic', None)
        if pic:
            # Verify file exists
            pic_path = os.path.join(app.root_path, 'static', 'uploads', 'profilepics', pic)
            if os.path.exists(pic_path):
                return pic
            else:
                print(f"Profile picture file not found: {pic_path}")
                return None
        return None

    @property
    def verified(self):
        return self.data.get('verified', False)

# Enhanced login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        
        # Verify user still exists in database
        if session['user_email'] not in users_db:
            session.clear()
            flash('Your session has expired. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

# Static file serving for uploaded images
@app.route('/static/uploads/profilepics/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Main Routes
@app.route('/')
def index():
    """Home page - redirect to dashboard if logged in, otherwise show login"""
    if 'user_email' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Enhanced user registration with staff support and persistent storage"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        id_number = request.form.get('id_number', '').strip()  # Student ID or Employee ID
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        user_type = request.form.get('user_type', 'student')
        
        # Enhanced validation
        if not all([name, email, phone, id_number, password]):
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        # Email validation based on user type
        if user_type == 'student' and not email.endswith('@student.xavier.ac.in'):
            flash('Students must use @student.xavier.ac.in email address.', 'error')
            return render_template('register.html')
        
        if user_type == 'staff' and not email.endswith('@xavier.ac.in'):
            flash('Staff must use @xavier.ac.in email address.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html')
        
        if email in users_db:
            flash('Email already registered. Please use a different email.', 'error')
            return render_template('register.html')
        
        if len(phone) < 10:
            flash('Please enter a valid phone number.', 'error')
            return render_template('register.html')
        
        # Create user account based on type
        user_data = {
            'name': name,
            'email': email,
            'password': hashlib.sha256(password.encode()).hexdigest(),
            'phone': phone,
            'department': '',
            'about': '',
            'profile_pic': None,
            'verified': True,
            'user_type': user_type
        }
        
        if user_type == 'student':
            user_data.update({
                'student_id': id_number,
                'year': 1,
                'gender': ''
            })
        else:  # staff
            user_data.update({
                'employee_id': id_number,
                'designation': '',
                'car_model': '',
                'max_passengers': 0
            })
        
        # Save to persistent database
        users_db[email] = user_data
        save_users_db(users_db)
        
        print(f"New {user_type} registered: {name} ({email})")
        flash('Registration successful! Please log in with your credentials.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Enhanced login with staff/student validation"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user_type = request.form.get('user_type', 'student')
        
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('login.html')
        
        # Validate email domain based on user type
        if user_type == 'student' and not email.endswith('@student.xavier.ac.in'):
            flash('Use only Institute E-Mail ID (@student.xavier.ac.in for students)', 'error')
            return render_template('login.html')
        
        if user_type == 'staff' and not email.endswith('@xavier.ac.in'):
            flash('Use only Institute E-Mail ID (@xavier.ac.in for staff)', 'error')
            return render_template('login.html')
        
        user_data = users_db.get(email)
        if user_data and user_data['password'] == hashlib.sha256(password.encode()).hexdigest():
            # Verify user type matches
            if user_data.get('user_type') != user_type:
                flash('Invalid user type selected. Please choose the correct account type.', 'error')
                return render_template('login.html')
            
            session['user_email'] = email
            print(f"User logged in: {user_data['name']} ({email})")
            flash(f"Welcome back, {user_data['name']}!", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Enhanced logout with session cleanup"""
    user_email = session.get('user_email', 'Unknown')
    session.clear()
    print(f"User logged out: {user_email}")
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Enhanced dashboard with ride statistics"""
    user = User(session['user_email'])
    
    # Calculate user's ride statistics
    user_rides = [ride for ride in sample_rides if ride['driver_email'] == user.email]
    
    stats = {
        'rides_offered': len(user_rides),
        'active_rides': len([r for r in user_rides if r['available_seats'] > 0]),
        'total_earnings': sum(ride['price_per_seat'] * (ride['total_seats'] - ride['available_seats']) for ride in user_rides)
    }
    
    return render_template('dashboard.html', user=user, stats=stats, user_rides=user_rides)

@app.route('/profile')
@login_required
def profile():
    """Enhanced profile page with earnings stats"""
    user = User(session['user_email'])
    
    # Calculate user's ride statistics for profile
    user_rides = [ride for ride in sample_rides if ride['driver_email'] == user.email]
    
    stats = {
        'rides_offered': len(user_rides),
        'active_rides': len([r for r in user_rides if r['available_seats'] > 0]),
        'total_earnings': sum(ride['price_per_seat'] * (ride['total_seats'] - ride['available_seats']) for ride in user_rides)
    }
    
    return render_template('profile.html', user=user, stats=stats)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Enhanced profile editing with car details for staff and persistent storage"""
    user = User(session['user_email'])
    
    if request.method == 'POST':
        # Common fields
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        about = request.form.get('about', '').strip()
        
        # User type specific fields
        if user.user_type == 'student':
            year = request.form.get('year', '').strip()
            gender = request.form.get('gender', '').strip()
            users_db[user.email].update({
                'year': int(year) if year.isdigit() else user.year,
                'gender': gender
            })
        else:  # staff
            designation = request.form.get('designation', '').strip()
            car_model = request.form.get('car_model', '').strip()
            max_passengers = request.form.get('max_passengers', '').strip()
            users_db[user.email].update({
                'designation': designation,
                'car_model': car_model,
                'max_passengers': int(max_passengers) if max_passengers.isdigit() else 0
            })
        
        # Update common fields
        users_db[user.email].update({
            'name': name or user.name,
            'phone': phone or user.phone,
            'department': department or user.department,
            'about': about or user.about
        })
        
        # Handle profile picture upload
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename != '' and allowed_file(file.filename):
                try:
                    picture_file = save_picture(file, user.email)
                    users_db[user.email]['profile_pic'] = picture_file
                    flash('Profile picture updated successfully!', 'success')
                except Exception as e:
                    flash(f'Error uploading profile picture: {str(e)}', 'error')
        
        # Save changes to persistent database
        save_users_db(users_db)
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html', user=user)

@app.route('/find_ride', methods=['GET'])
@login_required
def find_ride():
    """FIXED: Enhanced find ride that shows ALL rides from OTHER users"""
    user = User(session['user_email'])
    search_from = request.args.get('from', '').strip()
    search_to = request.args.get('to', '').strip()
    search_date = request.args.get('date', '').strip()
    
    # Start with ALL rides (this is the key fix)
    rides = sample_rides.copy()
    
    print(f"🔍 SEARCH DEBUG:")
    print(f"📧 Current user: {user.email}")
    print(f"📊 Total rides in database: {len(rides)}")
    print(f"🔍 Search filters - From: '{search_from}', To: '{search_to}', Date: '{search_date}'")
    
    # Apply search filters if provided
    if search_from:
        rides = [r for r in rides if search_from.lower() in r['from_location'].lower()]
        print(f"📍 After 'from' filter: {len(rides)} rides")
    
    if search_to:
        rides = [r for r in rides if search_to.lower() in r['to_location'].lower()]
        print(f"🏁 After 'to' filter: {len(rides)} rides")
    
    if search_date:
        rides = [r for r in rides if r['date'] == search_date]
        print(f"📅 After date filter: {len(rides)} rides")
    
    # Only show rides with available seats
    rides = [r for r in rides if r['available_seats'] > 0]
    print(f"💺 After seat availability filter: {len(rides)} rides")
    
    # IMPORTANT: Show rides from OTHER users (not your own rides in find section)
    rides = [r for r in rides if r['driver_email'] != user.email]
    print(f"👥 After removing own rides: {len(rides)} rides")
    
    # Debug: Print all rides for troubleshooting
    print(f"🚗 Final rides to display:")
    for i, ride in enumerate(rides, 1):
        print(f"   {i}. {ride['driver_name']}: {ride['from_location']} → {ride['to_location']} ({ride['driver_email']})")
    
    # Sort rides by date and time
    rides.sort(key=lambda x: (x['date'], x['departure_time']))
    
    return render_template('find_ride.html', user=user, rides=rides, 
                         search_from=search_from, search_to=search_to, search_date=search_date)

@app.route('/create_ride', methods=['GET', 'POST'])
@login_required
def create_ride():
    """Enhanced create ride with car details and persistent storage"""
    user = User(session['user_email'])
    
    if request.method == 'POST':
        from_location = request.form.get('from_location', '').strip()
        to_location = request.form.get('to_location', '').strip()
        departure_time = request.form.get('departure_time', '').strip()
        date = request.form.get('date', '').strip()
        available_seats = request.form.get('available_seats', '').strip()
        price_per_seat = request.form.get('price_per_seat', '').strip()
        car_model = request.form.get('car_model', '').strip()
        max_passengers = request.form.get('max_passengers', '').strip()
        additional_info = request.form.get('additional_info', '').strip()
        
        # Validation
        if not all([from_location, to_location, departure_time, date, available_seats, price_per_seat, car_model]):
            flash('Please fill in all required fields.', 'error')
            return render_template('create_ride.html', user=user)
        
        try:
            available_seats = int(available_seats)
            price_per_seat = float(price_per_seat)
            max_passengers = int(max_passengers) if max_passengers else available_seats
            
            if available_seats <= 0 or available_seats > 6:
                raise ValueError("Invalid seat count")
            if price_per_seat <= 0 or price_per_seat > 1000:
                raise ValueError("Invalid price")
                
        except ValueError:
            flash('Please enter valid numbers for seats and price.', 'error')
            return render_template('create_ride.html', user=user)
        
        # Generate unique ID for the new ride
        new_ride_id = max([ride['id'] for ride in sample_rides], default=0) + 1
        
        # Create new ride
        new_ride = {
            'id': new_ride_id,
            'driver_name': user.name,
            'driver_email': user.email,
            'from_location': from_location,
            'to_location': to_location,
            'departure_time': departure_time,
            'date': date,
            'available_seats': available_seats,
            'total_seats': max_passengers,
            'car_model': car_model,
            'price_per_seat': price_per_seat,
            'department': user.department,
            'year': f'{user.year}rd Year' if user.user_type == 'student' else None,
            'designation': user.designation if user.user_type == 'staff' else None,
            'rating': 5.0,  # Default rating for new rides
            'phone': user.phone,
            'additional_info': additional_info or 'No additional information provided'
        }
        
        sample_rides.append(new_ride)
        save_rides_db(sample_rides)  # Save to persistent database
        
        # Update user's car details in profile if they're staff or don't have it set
        if user.user_type == 'staff' or not user.car_model:
            users_db[user.email].update({
                'car_model': car_model,
                'max_passengers': max_passengers
            })
            save_users_db(users_db)
        
        print(f"✅ New ride created by {user.name}: {from_location} -> {to_location} (ID: {new_ride_id})")
        flash('Ride created successfully! Other users can now find and book your ride.', 'success')
        return redirect(url_for('my_rides'))
    
    return render_template('create_ride.html', user=user)

@app.route('/my_rides')
@login_required
def my_rides():
    """Enhanced my rides page with edit/delete functionality"""
    user = User(session['user_email'])
    user_rides = [ride for ride in sample_rides if ride['driver_email'] == user.email]
    
    # Sort rides by date and time
    user_rides.sort(key=lambda x: (x['date'], x['departure_time']), reverse=True)
    
    print(f"📋 My Rides for {user.name}: {len(user_rides)} rides found")
    
    return render_template('my_rides.html', user=user, rides=user_rides)

@app.route('/edit_ride/<int:ride_id>', methods=['GET', 'POST'])
@login_required
def edit_ride(ride_id):
    """Edit a ride with persistent storage"""
    user = User(session['user_email'])
    
    # Find the ride
    ride = next((r for r in sample_rides if r['id'] == ride_id and r['driver_email'] == user.email), None)
    
    if not ride:
        flash('Ride not found or you do not have permission to edit it.', 'error')
        return redirect(url_for('my_rides'))
    
    if request.method == 'POST':
        # Update ride details
        from_location = request.form.get('from_location', '').strip()
        to_location = request.form.get('to_location', '').strip()
        departure_time = request.form.get('departure_time', '').strip()
        date = request.form.get('date', '').strip()
        available_seats = request.form.get('available_seats', '').strip()
        price_per_seat = request.form.get('price_per_seat', '').strip()
        car_model = request.form.get('car_model', '').strip()
        max_passengers = request.form.get('max_passengers', '').strip()
        additional_info = request.form.get('additional_info', '').strip()
        
        if not all([from_location, to_location, departure_time, date, available_seats, price_per_seat, car_model]):
            flash('Please fill in all required fields.', 'error')
            return render_template('edit_ride.html', user=user, ride=ride)
        
        try:
            available_seats = int(available_seats)
            price_per_seat = float(price_per_seat)
            max_passengers = int(max_passengers) if max_passengers else available_seats
        except ValueError:
            flash('Please enter valid numbers for seats and price.', 'error')
            return render_template('edit_ride.html', user=user, ride=ride)
        
        # Update the ride
        ride.update({
            'from_location': from_location,
            'to_location': to_location,
            'departure_time': departure_time,
            'date': date,
            'available_seats': available_seats,
            'total_seats': max_passengers,
            'car_model': car_model,
            'price_per_seat': price_per_seat,
            'additional_info': additional_info or 'No additional information provided'
        })
        
        # Save changes to persistent database
        save_rides_db(sample_rides)
        
        print(f"✅ Ride updated by {user.name}: {from_location} -> {to_location}")
        flash('Ride updated successfully!', 'success')
        return redirect(url_for('my_rides'))
    
    return render_template('edit_ride.html', user=user, ride=ride)

@app.route('/book_ride/<int:ride_id>')
@login_required
def book_ride(ride_id):
    """Enhanced ride booking with persistent storage and notifications"""
    user = User(session['user_email'])
    
    # Find the ride
    ride = next((r for r in sample_rides if r['id'] == ride_id), None)
    
    if not ride:
        flash('Ride not found.', 'error')
        return redirect(url_for('find_ride'))
    
    if ride['available_seats'] <= 0:
        flash('Sorry, this ride is full.', 'error')
        return redirect(url_for('find_ride'))
    
    if ride['driver_email'] == user.email:
        flash('You cannot book your own ride.', 'error')
        return redirect(url_for('find_ride'))
    
    # Book the ride (decrease available seats)
    ride['available_seats'] -= 1
    save_rides_db(sample_rides)  # Save changes to persistent database
    
    print(f"🎫 Ride booked by {user.name} for ride {ride_id} ({ride['from_location']} -> {ride['to_location']})")
    flash(f'Successfully booked ride from {ride["from_location"]} to {ride["to_location"]}! Contact {ride["driver_name"]} at {ride["phone"]}.', 'success')
    return redirect(url_for('find_ride'))

@app.route('/cancel_ride/<int:ride_id>')
@login_required
def cancel_ride(ride_id):
    """Cancel a ride - Enhanced with proper deletion and persistent storage"""
    user = User(session['user_email'])
    
    # Find and remove the ride
    global sample_rides
    ride = next((r for r in sample_rides if r['id'] == ride_id and r['driver_email'] == user.email), None)
    
    if ride:
        sample_rides = [r for r in sample_rides if r['id'] != ride_id]
        save_rides_db(sample_rides)  # Save changes to persistent database
        print(f"❌ Ride deleted by {user.name}: {ride['from_location']} -> {ride['to_location']}")
        flash('Ride cancelled successfully.', 'success')
    else:
        flash('Ride not found or you do not have permission to cancel it.', 'error')
    
    return redirect(url_for('my_rides'))

# Debug route to check all rides (for troubleshooting)
@app.route('/debug/rides')
@login_required
def debug_rides():
    """Debug route to check all rides in database"""
    user = User(session['user_email'])
    rides_info = []
    
    for ride in sample_rides:
        rides_info.append({
            'id': ride['id'],
            'driver': ride['driver_name'],
            'email': ride['driver_email'],
            'route': f"{ride['from_location']} → {ride['to_location']}",
            'date': ride['date'],
            'seats': f"{ride['available_seats']}/{ride['total_seats']}"
        })
    
    return f"""
    <h1>🔍 DEBUG: All Rides in Database</h1>
    <p><strong>Current User:</strong> {user.name} ({user.email})</p>
    <p><strong>Total Rides:</strong> {len(sample_rides)}</p>
    <hr>
    {''.join([f"<p><strong>ID {r['id']}:</strong> {r['driver']} ({r['email']}) - {r['route']} on {r['date']} - Seats: {r['seats']}</p>" for r in rides_info])}
    <hr>
    <a href="/dashboard">← Back to Dashboard</a>
    """

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    flash('Page not found.', 'error')
    return redirect(url_for('index'))

@app.errorhandler(405)
def method_not_allowed_error(error):
    """Handle Method Not Allowed errors - FIX FOR FIND RIDE ISSUE"""
    flash('Invalid request method.', 'error')
    return redirect(url_for('find_ride'))

@app.errorhandler(500)
def internal_error(error):
    flash('An internal error occurred. Please try again.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("=" * 60)
    print(" LIFTLINK CARPOOL - ENHANCED VERSION 8.2")
    print("=" * 60)
    print("Local URL: http://127.0.0.1:5000")
    print("Network URL: http://localhost:5000")
    print("Xavier's Institute of Engineering")
    print("Sustainable Commute Hub - FIXED RIDE SHARING!")
    print("=" * 60)
    print("✅ ENHANCED FEATURES:")
    print("- 🔒 PERSISTENT USER REGISTRATION (No more re-registering!)")
    print("- 💾 FILE-BASED USER & RIDES STORAGE")
    print("- 🔄 AUTO-SAVE ON ALL CHANGES")
    print("- 🚀 SURVIVES SERVER RESTARTS")
    print("- 🎯 FIXED: Users can now see rides from OTHER users!")
    print("- 🔍 ENHANCED SEARCH: Smart filtering and debugging")
    print("- 👥 PROPER RIDE SHARING: Shubham can see Durvesh's rides!")
    print("- 🎫 WORKING BOOKING SYSTEM: Book rides from other users")
    print("- Clean Navigation (Dashboard/Profile/Logout boxes)")
    print("- XIE Logo in Header")
    print("- Fixed Find Ride Search (Method Not Allowed resolved)")
    print("- My Rides Edit/Delete Functionality")
    print("- Earnings Section in Profile")
    print("- Animated Background Bubbles")
    print("- Enhanced Typography (Playfair Display)")
    
    print(f"- Sample Routes: {len(sample_rides)} rides loaded")
    print(f"- Registered Users: {len(users_db)} users available")
    print("=" * 60)
    print("🔐 TEST LOGIN CREDENTIALS:")
    print("Student - Email: test@student.xavier.ac.in")
    print("Staff - Email: john.doe@xavier.ac.in")
    print("Additional Staff - Email: priya.patil@xavier.ac.in")
    print("Password: password123 / staff123")
    print("=" * 60)
    print("💾 DATABASE FILES:")
    print(f"- Users: {USERS_DB_FILE}")
    print(f"- Rides: {RIDES_DB_FILE}")
    print("=" * 60)
    print("🎉 FIXED ISSUE: Ride sharing now works perfectly!")
    print("✅ Durvesh creates ride → Shubham can find & book it!")
    print("🔍 Debug URL: http://localhost:5000/debug/rides")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True, threaded=True)
