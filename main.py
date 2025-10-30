# LiftLink Carpool - Enhanced Flask Web Application with One Booking Per User + Emergency Contacts
# Spyder Compatible - Xavier's Institute of Engineering - Sustainable Commute Hub
# Version 10.0 - One Booking Per User, Emergency Contacts, Enhanced Communication

import os
import sys
import json
import urllib.parse
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify
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
print(" LIFTLINK CARPOOL - ENHANCED VERSION 10.0")
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
app.secret_key = 'xie-liftlink-secretkey-2025-enhanced-v10'

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
BOOKINGS_DB_FILE = 'data/bookings_db.json'
EARNINGS_DB_FILE = 'data/earnings_db.json'

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

def load_bookings_db():
    """Load bookings database from JSON file"""
    try:
        if os.path.exists(BOOKINGS_DB_FILE):
            with open(BOOKINGS_DB_FILE, 'r', encoding='utf-8') as f:
                bookings_data = json.load(f)
                print(f"✓ Loaded {len(bookings_data)} bookings from database")
                return bookings_data
        else:
            print("Creating new bookings database...")
            return []
    except Exception as e:
        print(f"✗ Error loading bookings database: {e}")
        return []

def save_bookings_db(bookings_data):
    """Save bookings database to JSON file"""
    try:
        with open(BOOKINGS_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(bookings_data, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved {len(bookings_data)} bookings to database")
        return True
    except Exception as e:
        print(f"✗ Error saving bookings database: {e}")
        return False

def load_earnings_db():
    """Load earnings database from JSON file"""
    try:
        if os.path.exists(EARNINGS_DB_FILE):
            with open(EARNINGS_DB_FILE, 'r', encoding='utf-8') as f:
                earnings_data = json.load(f)
                print(f"✓ Loaded earnings data from database")
                return earnings_data
        else:
            print("Creating new earnings database...")
            return {}
    except Exception as e:
        print(f"✗ Error loading earnings database: {e}")
        return {}

def save_earnings_db(earnings_data):
    """Save earnings database to JSON file"""
    try:
        with open(EARNINGS_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(earnings_data, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved earnings data to database")
        return True
    except Exception as e:
        print(f"✗ Error saving earnings database: {e}")
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
            'emergency_contact_name': 'Rajesh Bedre',
            'emergency_contact_phone': '9876543210',
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
            'emergency_contact_name': 'Jane Doe',
            'emergency_contact_phone': '9876543211',
            'employee_id': 'XIE001',
            'department': 'Computer Science Engg',
            'designation': 'Assistant Professor',
            'about': 'Assistant Professor in Computer Engineering Department.',
            'profile_pic': None,
            'verified': True,
            'user_type': 'staff',
            'car_model': 'Honda City',
            'max_passengers': 3
        }
    }

def get_default_rides():
    """Get default rides for first-time setup"""
    today = datetime.now().strftime('%Y-%m-%d')
    return [
        {
            'id': 1,
            'driver_name': 'Durvesh Bedre',
            'driver_email': 'test@student.xavier.ac.in',
            'from_location': 'Dadar Railway Station',
            'to_location': 'Xavier Institute of Engineering, Mahim',
            'departure_time': '08:00',
            'date': today,
            'available_seats': 3,
            'total_seats': 4,
            'car_model': 'Honda City',
            'price_per_seat': 25,
            'department': 'Electronics & Telecommunication Engg',
            'year': '4th Year',
            'rating': 4.5,
            'phone': '7700090035',
            'additional_info': 'Pickup near main gate, AC available'
        }
    ]

# Initialize persistent databases
users_db = load_users_db()
sample_rides = load_rides_db()
bookings_db = load_bookings_db()
earnings_db = load_earnings_db()

class User:
    """Enhanced User class with emergency contacts"""
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
    def emergency_contact_name(self):
        return self.data.get('emergency_contact_name', '')

    @property
    def emergency_contact_phone(self):
        return self.data.get('emergency_contact_phone', '')

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

# Enhanced Booking Helper Functions
def check_user_booking_status(user_email, ride_id):
    """Check if user has already booked this ride"""
    user_bookings = [booking for booking in bookings_db if 
                    booking['passenger_email'] == user_email and 
                    booking['ride_id'] == ride_id and 
                    booking['status'] == 'confirmed']
    return len(user_bookings) > 0

def get_user_booking_for_ride(user_email, ride_id):
    """Get user's booking for a specific ride"""
    user_booking = next((booking for booking in bookings_db if 
                        booking['passenger_email'] == user_email and 
                        booking['ride_id'] == ride_id and 
                        booking['status'] == 'confirmed'), None)
    return user_booking

# Communication Helper Functions
def generate_whatsapp_url(phone, message):
    """Generate WhatsApp URL with pre-filled message"""
    # Remove any non-digit characters and ensure proper format
    phone_clean = ''.join(filter(str.isdigit, phone))
    if phone_clean.startswith('0'):
        phone_clean = '91' + phone_clean[1:]
    elif not phone_clean.startswith('91'):
        phone_clean = '91' + phone_clean
    
    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://wa.me/{phone_clean}?text={encoded_message}"
    return whatsapp_url

def generate_maps_url(from_location, to_location):
    """Generate Google Maps URL for route"""
    encoded_from = urllib.parse.quote(from_location)
    encoded_to = urllib.parse.quote(to_location)
    maps_url = f"https://www.google.com/maps/dir/{encoded_from}/{encoded_to}"
    return maps_url

def add_earning_record(driver_email, passenger_name, passenger_email, amount, ride_details):
    """Add earning record to earnings history"""
    if driver_email not in earnings_db:
        earnings_db[driver_email] = []
    
    earning_record = {
        'id': len(earnings_db.get(driver_email, [])) + 1,
        'passenger_name': passenger_name,
        'passenger_email': passenger_email,
        'amount': amount,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'time': datetime.now().strftime('%H:%M'),
        'ride_from': ride_details['from_location'],
        'ride_to': ride_details['to_location'],
        'ride_date': ride_details['date'],
        'ride_time': ride_details['departure_time']
    }
    
    earnings_db[driver_email].append(earning_record)
    save_earnings_db(earnings_db)
    print(f"💰 Earning recorded: {driver_email} earned ₹{amount} from {passenger_name}")

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
    """Enhanced user registration with emergency contacts"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        emergency_name = request.form.get('emergency_contact_name', '').strip()
        emergency_phone = request.form.get('emergency_contact_phone', '').strip()
        id_number = request.form.get('id_number', '').strip()  # Student ID or Employee ID
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        user_type = request.form.get('user_type', 'student')
        
        # Enhanced validation
        if not all([name, email, phone, emergency_name, emergency_phone, id_number, password]):
            flash('All fields including emergency contact are required.', 'error')
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
        
        if len(emergency_phone) < 10:
            flash('Please enter a valid emergency contact phone number.', 'error')
            return render_template('register.html')
        
        # Create user account based on type
        user_data = {
            'name': name,
            'email': email,
            'password': hashlib.sha256(password.encode()).hexdigest(),
            'phone': phone,
            'emergency_contact_name': emergency_name,
            'emergency_contact_phone': emergency_phone,
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
    """Enhanced profile page with earnings stats and history"""
    user = User(session['user_email'])
    
    # Calculate user's ride statistics for profile
    user_rides = [ride for ride in sample_rides if ride['driver_email'] == user.email]
    
    stats = {
        'rides_offered': len(user_rides),
        'active_rides': len([r for r in user_rides if r['available_seats'] > 0]),
        'total_earnings': sum(ride['price_per_seat'] * (ride['total_seats'] - ride['available_seats']) for ride in user_rides)
    }
    
    # Get earnings history
    earnings_history = earnings_db.get(user.email, [])
    earnings_history.sort(key=lambda x: (x['date'], x['time']), reverse=True)
    
    return render_template('profile.html', user=user, stats=stats, earnings_history=earnings_history)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Enhanced profile editing with emergency contacts"""
    user = User(session['user_email'])
    
    if request.method == 'POST':
        # Common fields
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        emergency_name = request.form.get('emergency_contact_name', '').strip()
        emergency_phone = request.form.get('emergency_contact_phone', '').strip()
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
            'emergency_contact_name': emergency_name or user.emergency_contact_name,
            'emergency_contact_phone': emergency_phone or user.emergency_contact_phone,
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
    """Enhanced find ride with booking status checking"""
    user = User(session['user_email'])
    search_from = request.args.get('from', '').strip()
    search_to = request.args.get('to', '').strip()
    search_date = request.args.get('date', '').strip()
    
    # Start with ALL rides
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
    
    # Show rides from OTHER users (not your own rides in find section)
    rides = [r for r in rides if r['driver_email'] != user.email]
    print(f"👥 After removing own rides: {len(rides)} rides")
    
    # Add communication URLs and booking status to each ride
    for ride in rides:
        # Check if current user has already booked this ride
        user_has_booked = check_user_booking_status(user.email, ride['id'])
        user_booking = get_user_booking_for_ride(user.email, ride['id'])
        
        ride['user_has_booked'] = user_has_booked
        ride['user_booking'] = user_booking
        
        # WhatsApp message
        if user_has_booked:
            whatsapp_message = f"Hi {ride['driver_name']}, this is {user.name}. I have already booked your ride from {ride['from_location']} to {ride['to_location']} on {ride['date']} at {ride['departure_time']}. Please let me know the pickup details."
        else:
            whatsapp_message = f"Hi {ride['driver_name']}, I'm interested in your ride from {ride['from_location']} to {ride['to_location']} on {ride['date']} at {ride['departure_time']}. Can we coordinate for pickup?"
        
        ride['whatsapp_url'] = generate_whatsapp_url(ride['phone'], whatsapp_message)
        
        # Maps URL for route
        ride['maps_url'] = generate_maps_url(ride['from_location'], ride['to_location'])
        
        # Phone call URL
        ride['call_url'] = f"tel:{ride['phone']}"
    
    # Debug: Print all rides for troubleshooting
    print(f"🚗 Final rides to display:")
    for i, ride in enumerate(rides, 1):
        booked_status = "BOOKED" if ride.get('user_has_booked', False) else "AVAILABLE"
        print(f"   {i}. {ride['driver_name']}: {ride['from_location']} → {ride['to_location']} ({booked_status})")
    
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
    """Enhanced ride booking with one booking per user restriction"""
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
    
    # Check if user has already booked this ride
    if check_user_booking_status(user.email, ride_id):
        flash('You have already booked this ride. You can only book one seat per ride.', 'error')
        return redirect(url_for('find_ride'))
    
    # Book the ride (decrease available seats)
    ride['available_seats'] -= 1
    
    # Create booking record
    booking = {
        'id': len(bookings_db) + 1,
        'ride_id': ride_id,
        'passenger_name': user.name,
        'passenger_email': user.email,
        'passenger_phone': user.phone,
        'driver_name': ride['driver_name'],
        'driver_email': ride['driver_email'],
        'driver_phone': ride['phone'],
        'from_location': ride['from_location'],
        'to_location': ride['to_location'],
        'date': ride['date'],
        'departure_time': ride['departure_time'],
        'price_paid': ride['price_per_seat'],
        'booking_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'confirmed'
    }
    
    bookings_db.append(booking)
    
    # Add earning record for driver
    add_earning_record(
        driver_email=ride['driver_email'],
        passenger_name=user.name,
        passenger_email=user.email,
        amount=ride['price_per_seat'],
        ride_details=ride
    )
    
    # Save all changes
    save_rides_db(sample_rides)
    save_bookings_db(bookings_db)
    
    # Generate communication URLs
    whatsapp_message = f"Hi {ride['driver_name']}, I've booked your ride from {ride['from_location']} to {ride['to_location']} on {ride['date']} at {ride['departure_time']}. My name is {user.name} and my phone is {user.phone}. Looking forward to the ride!"
    whatsapp_url = generate_whatsapp_url(ride['phone'], whatsapp_message)
    call_url = f"tel:{ride['phone']}"
    maps_url = generate_maps_url(ride['from_location'], ride['to_location'])
    
    print(f"🎫 Ride booked by {user.name} for ride {ride_id} ({ride['from_location']} -> {ride['to_location']})")
    
    # Success message with communication options
    success_message = f"""
    <div style="text-align: center; padding: 2rem;">
        <h3 style="color: #10B981; margin-bottom: 1rem;">🎉 Ride Booked Successfully!</h3>
        <p><strong>Route:</strong> {ride['from_location']} → {ride['to_location']}</p>
        <p><strong>Date & Time:</strong> {ride['date']} at {ride['departure_time']}</p>
        <p><strong>Driver:</strong> {ride['driver_name']}</p>
        <p><strong>Price:</strong> ₹{ride['price_per_seat']}</p>
        <hr style="margin: 2rem 0;">
        <h4 style="color: #667eea;">📞 Contact Driver:</h4>
        <div style="margin: 1rem 0;">
            <a href="{whatsapp_url}" target="_blank" style="display: inline-block; background: #25D366; color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; margin: 5px;">
                📱 WhatsApp Driver
            </a>
            <a href="{call_url}" style="display: inline-block; background: #007bff; color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; margin: 5px;">
                📞 Call Driver
            </a>
        </div>
        <h4 style="color: #667eea; margin-top: 2rem;">🗺️ View Route:</h4>
        <div style="margin: 1rem 0;">
            <a href="{maps_url}" target="_blank" style="display: inline-block; background: #4285F4; color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; margin: 5px;">
                🗺️ View on Google Maps
            </a>
        </div>
        <p style="margin-top: 2rem; color: #666;">
            <strong>Phone:</strong> {ride['phone']}<br>
            <strong>Note:</strong> You can only book one seat per ride.<br>
            Have a safe journey! 🚗
        </p>
    </div>
    """
    
    flash(success_message, 'success')
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

@app.route('/earnings_history')
@login_required
def earnings_history():
    """View detailed earnings history"""
    user = User(session['user_email'])
    
    # Get earnings history for current user
    user_earnings = earnings_db.get(user.email, [])
    user_earnings.sort(key=lambda x: (x['date'], x['time']), reverse=True)
    
    # Calculate statistics
    total_earnings = sum(earning['amount'] for earning in user_earnings)
    total_passengers = len(user_earnings)
    
    return render_template('earnings_history.html', 
                         user=user, 
                         earnings=user_earnings,
                         total_earnings=total_earnings,
                         total_passengers=total_passengers)

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
    <p><strong>Total Bookings:</strong> {len(bookings_db)}</p>
    <p><strong>Total Earnings Records:</strong> {len(earnings_db)}</p>
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
    print(" LIFTLINK CARPOOL - ENHANCED VERSION 10.0")
    print("=" * 60)
    print("Local URL: http://127.0.0.1:5000")
    print("Network URL: http://localhost:5000")
    print("Xavier's Institute of Engineering")
    print("Sustainable Commute Hub - ONE BOOKING PER USER + EMERGENCY CONTACTS!")
    print("=" * 60)
    print("✅ ENHANCED FEATURES:")
    print("- 🔒 ONE BOOKING PER USER PER RIDE")
    print("- 🚨 EMERGENCY CONTACT REGISTRATION")
    print("- 📱 ENHANCED WHATSAPP + CALL INTEGRATION")
    print("- 🗺️ GOOGLE MAPS ROUTE INTEGRATION")
    print("- 💰 DETAILED EARNINGS HISTORY")
    print("- 🎫 SMART BOOKING STATUS TRACKING")
    print("- 👥 PROPER RIDE SHARING")
    print("- 🔍 SMART SEARCH & FILTERING")
    print("- 📊 COMPREHENSIVE ANALYTICS")
    
    print(f"- Sample Routes: {len(sample_rides)} rides loaded")
    print(f"- Registered Users: {len(users_db)} users available")
    print(f"- Total Bookings: {len(bookings_db)} bookings recorded")
    print(f"- Earnings Records: {len(earnings_db)} drivers have earnings")
    print("=" * 60)
    print("🔐 TEST LOGIN CREDENTIALS:")
    print("Student - Email: test@student.xavier.ac.in")
    print("Staff - Email: john.doe@xavier.ac.in")
    print("Password: password123 / staff123")
    print("=" * 60)
    print("💾 DATABASE FILES:")
    print(f"- Users: {USERS_DB_FILE}")
    print(f"- Rides: {RIDES_DB_FILE}")
    print(f"- Bookings: {BOOKINGS_DB_FILE}")
    print(f"- Earnings: {EARNINGS_DB_FILE}")
    print("=" * 60)
    print("🎉 NEW FEATURES ADDED:")
    print("✅ One booking per user per ride restriction")
    print("✅ Emergency contact during registration")
    print("✅ Enhanced booking status tracking")
    print("✅ Smart contact options based on booking status")
    print("✅ Improved booking confirmation messages")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True, threaded=True)
