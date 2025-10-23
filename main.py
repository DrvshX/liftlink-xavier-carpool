"""
LiftLink Carpool - Enhanced Flask Web Application (Spyder Compatible)
Xavier's Institute of Engineering - Sustainable Commute Hub
Version 6.2 - Complete with FIXED Profile Picture Support & Google Maps
"""

import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from functools import wraps
import hashlib
import secrets
from datetime import datetime

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

print("="*60)
print("🚗 LIFTLINK CARPOOL - GOOGLE MAPS VERSION")
print("="*60)
print(f"Current directory: {os.getcwd()}")
print(f"Templates exist: {os.path.exists('templates')}")
print(f"Static folder exists: {os.path.exists('static')}")

if os.path.exists('templates'):
    try:
        print(f"Template files: {os.listdir('templates')}")
    except PermissionError:
        print("Permission denied accessing templates folder")

print("="*60)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'xie-liftlink-secretkey-2025-profilepic-googlemaps'

# Profile Picture Configuration
UPLOAD_FOLDER = 'static/uploads/profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('static/images', exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Profile Picture Helper Functions
def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_picture(form_picture, current_user_email):
    """Save and optionally resize profile picture"""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = f"{current_user_email.replace('@', '_').replace('.', '_')}_{random_hex}{f_ext}"
    picture_path = os.path.join(app.root_path, 'static', 'uploads', 'profile_pics', picture_fn)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    
    if PIL_AVAILABLE:
        output_size = (300, 300)
        try:
            img = Image.open(form_picture)
            # Convert to RGB if it's RGBA (for PNG with transparency)
            if img.mode == "RGBA":
                img = img.convert("RGB")
            img.thumbnail(output_size, Image.Resampling.LANCZOS)
            img.save(picture_path, quality=90, optimize=True)
            print(f"✅ Profile picture saved and resized: {picture_fn}")
        except Exception as e:
            print(f"❌ PIL resize failed, saving directly: {e}")
            form_picture.save(picture_path)
    else:
        # If PIL is not available, just save the file directly
        form_picture.save(picture_path)
        print(f"✅ Profile picture saved: {picture_fn}")
    
    # Verify file was saved
    if os.path.exists(picture_path):
        file_size = os.path.getsize(picture_path)
        print(f"✅ File saved successfully: {picture_path} ({file_size} bytes)")
    else:
        print(f"❌ File NOT saved: {picture_path}")
    
    return picture_fn

# Enhanced user database with more test users
users_db = {
    'test@student.xavier.ac.in': {
        'name': 'Durvesh Bedre',
        'email': 'test@student.xavier.ac.in',
        'password': hashlib.sha256('password123'.encode()).hexdigest(),
        'phone': '7700090035',
        'student_id': '2023032002',
        'department': 'Electronics & Telecommunication',
        'year': 4,
        'gender': 'Male',
        'about': 'Final year ETC student interested in sustainable transportation.',
        'profile_pic': None,
        'verified': True
    },
    '2023032002.durveshvsb@student.xavier.ac.in': {
        'name': 'Durvesh Bedre',
        'email': '2023032002.durveshvsb@student.xavier.ac.in',
        'password': hashlib.sha256('password123'.encode()).hexdigest(),
        'phone': '7700090035',
        'student_id': '2023032002',
        'department': 'Electronics & Telecommunication',
        'year': 4,
        'gender': 'Male',
        'about': 'Final year ETC student interested in sustainable transportation and carpooling.',
        'profile_pic': None,
        'verified': True
    },
    'admin@student.xavier.ac.in': {
        'name': 'Admin User',
        'email': 'admin@student.xavier.ac.in',
        'password': hashlib.sha256('admin123'.encode()).hexdigest(),
        'phone': '9876543210',
        'student_id': '2023000001',
        'department': 'Computer Engineering',
        'year': 4,
        'gender': 'Male',
        'about': 'System Administrator',
        'profile_pic': None,
        'verified': True
    }
}

# Enhanced sample rides data
sample_rides = [
    {
        'id': 1,
        'driver_name': 'Rohit Sharma',
        'driver_email': '2023032001.rohit@student.xavier.ac.in',
        'from_location': 'Vashi Station',
        'to_location': 'Xavier Institute of Engineering',
        'departure_time': '08:00 AM',
        'date': '2025-10-24',
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
        'driver_name': 'Priya Patil',
        'driver_email': '2023032034.priya@student.xavier.ac.in',
        'from_location': 'Nerul Station',
        'to_location': 'Xavier Institute of Engineering',
        'departure_time': '08:15 AM',
        'date': '2025-10-24',
        'available_seats': 2,
        'total_seats': 4,
        'car_model': 'Maruti Swift',
        'price_per_seat': 20,
        'department': 'Electronics & Telecom',
        'year': '4th Year',
        'rating': 4.8,
        'phone': '9876543211',
        'additional_info': 'Regular route, music system available'
    },
    {
        'id': 3,
        'driver_name': 'Kiran Desai',
        'driver_email': '2023032080.kiran@student.xavier.ac.in',
        'from_location': 'Dadar Station',
        'to_location': 'Xavier Institute of Engineering',
        'departure_time': '08:30 AM',
        'date': '2025-10-24',
        'available_seats': 2,
        'total_seats': 4,
        'car_model': 'Hyundai Creta',
        'price_per_seat': 35,
        'department': 'Mechanical Engineering',
        'year': '3rd Year',
        'rating': 4.4,
        'phone': '9876543280',
        'additional_info': 'Express route via Eastern Express Highway'
    }
]

# Enhanced User class with better property handling
class User:
    def __init__(self, email):
        self.email = email
        self.data = users_db.get(email, {})
        if not self.data:
            print(f"❌ User not found in database: {email}")
    
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
    def department(self):
        return self.data.get('department', '')
    
    @property
    def year(self):
        return self.data.get('year', 1)
    
    @property
    def gender(self):
        return self.data.get('gender', '')
    
    @property
    def about(self):
        return self.data.get('about', '')
    
    @property
    def profile_pic(self):
        pic = self.data.get('profile_pic', None)
        if pic:
            # Verify file exists
            pic_path = os.path.join(app.root_path, 'static', 'uploads', 'profile_pics', pic)
            if os.path.exists(pic_path):
                return pic
            else:
                print(f"❌ Profile picture file not found: {pic_path}")
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
@app.route('/static/uploads/profile_pics/<filename>')
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
    """User registration with enhanced validation"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        student_id = request.form.get('student_id', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Enhanced validation
        if not all([name, email, phone, student_id, password]):
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        if not email.endswith('@student.xavier.ac.in'):
            flash('Please use your Xavier Institute email address (@student.xavier.ac.in).', 'error')
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
        
        # Create user account
        users_db[email] = {
            'name': name,
            'email': email,
            'password': hashlib.sha256(password.encode()).hexdigest(),
            'phone': phone,
            'student_id': student_id,
            'department': '',
            'year': 1,
            'gender': '',
            'about': '',
            'profile_pic': None,
            'verified': True
        }
        
        print(f"✅ New user registered: {name} ({email})")
        flash('Registration successful! Please log in with your credentials.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Enhanced login with better security"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('login.html')
        
        user_data = users_db.get(email)
        if user_data and user_data['password'] == hashlib.sha256(password.encode()).hexdigest():
            session['user_email'] = email
            print(f"✅ User logged in: {user_data['name']} ({email})")
            flash(f'Welcome back, {user_data["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Enhanced logout with session cleanup"""
    user_email = session.get('user_email', 'Unknown')
    session.clear()
    print(f"✅ User logged out: {user_email}")
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Enhanced dashboard with user statistics"""
    user = User(session['user_email'])
    
    # Calculate user statistics
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
    """Enhanced profile page with detailed information"""
    user = User(session['user_email'])
    
    # Calculate user statistics
    user_rides = [ride for ride in sample_rides if ride['driver_email'] == user.email]
    total_rides = len(user_rides)
    total_seats_shared = sum(ride['total_seats'] - ride['available_seats'] for ride in user_rides)
    total_earnings = sum(ride['price_per_seat'] * (ride['total_seats'] - ride['available_seats']) for ride in user_rides)
    
    stats = {
        'total_rides': total_rides,
        'total_seats_shared': total_seats_shared,
        'total_earnings': total_earnings,
        'avg_rating': 4.5,  # Calculate profile statistics
    }
    
    print(f"🔍 Profile Debug - User: {user.email}, Profile Pic: {user.profile_pic}")
    if user.profile_pic:
        pic_path = os.path.join(app.root_path, 'static', 'uploads', 'profile_pics', user.profile_pic)
        print(f"🔍 Profile Pic Path: {pic_path}, Exists: {os.path.exists(pic_path)}")
    
    return render_template('profile.html', user=user, user_rides=user_rides, stats=stats)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """ENHANCED profile editing with FIXED profile picture support"""
    user = User(session['user_email'])
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        year = request.form.get('year', 1)
        about = request.form.get('about', '').strip()
        
        # Validate required fields
        if not name:
            flash('Name is required.', 'error')
            return render_template('edit_profile.html', user=user)
        
        if not phone:
            flash('Phone number is required.', 'error')
            return render_template('edit_profile.html', user=user)
        
        # ENHANCED Profile Picture Handling with DEBUGGING
        profile_pic_filename = None
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            print(f"📁 File received: {file.filename}, Size: {len(file.read()) if file else 0}")
            file.seek(0)  # Reset file pointer after reading
            
            if file and file.filename != '' and allowed_file(file.filename):
                try:
                    print("📸 Processing profile picture upload...")
                    
                    # Delete old profile picture if exists
                    old_pic = users_db[session['user_email']].get('profile_pic')
                    if old_pic:
                        old_path = os.path.join(app.root_path, 'static', 'uploads', 'profile_pics', old_pic)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                            print(f"🗑️ Deleted old profile picture: {old_pic}")
                    
                    # Save new picture with enhanced error handling
                    profile_pic_filename = save_picture(file, session['user_email'])
                    
                    # VERIFY file was saved properly
                    saved_path = os.path.join(app.root_path, 'static', 'uploads', 'profile_pics', profile_pic_filename)
                    if os.path.exists(saved_path):
                        file_size = os.path.getsize(saved_path)
                        print(f"✅ Profile picture VERIFIED: {profile_pic_filename} ({file_size} bytes)")
                        
                        # Test URL generation
                        pic_url = url_for('static', filename=f'uploads/profile_pics/{profile_pic_filename}')
                        print(f"🌐 Profile picture URL: {pic_url}")
                    else:
                        print(f"❌ Profile picture file NOT FOUND after save: {saved_path}")
                        flash('Error: Profile picture was not saved properly. Please try again.', 'error')
                        return render_template('edit_profile.html', user=user)
                        
                except Exception as e:
                    flash(f'Error uploading profile picture: {str(e)}', 'error')
                    print(f"❌ Profile picture upload error: {e}")
                    import traceback
                    traceback.print_exc()
                    return render_template('edit_profile.html', user=user)
            
            elif file and file.filename != '':
                flash('Please upload a valid image file (PNG, JPG, JPEG, or GIF).', 'error')
                return render_template('edit_profile.html', user=user)
        
        # Update user data in database
        email = session['user_email']
        users_db[email]['name'] = name
        users_db[email]['phone'] = phone
        users_db[email]['department'] = department
        users_db[email]['year'] = year
        users_db[email]['about'] = about
        
        if profile_pic_filename:
            users_db[email]['profile_pic'] = profile_pic_filename
            print(f"💾 Database updated with profile picture: {profile_pic_filename}")
        
        # Debug Print user data
        print(f"💾 Updated user data for: {email}")
        print(f"   - Name: {users_db[email]['name']}")
        print(f"   - Phone: {users_db[email]['phone']}")
        print(f"   - Department: {users_db[email]['department']}")
        print(f"   - Profile Pic: {users_db[email]['profile_pic']}")
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html', user=user)

@app.route('/find_ride', methods=['GET', 'POST'])
@login_required
def find_ride():
    """Enhanced Find available rides with Google Maps support"""
    user = User(session['user_email'])
    available_rides = []
    
    if request.method == 'POST':
        from_location = request.form.get('from_location', '').strip()
        to_location = request.form.get('to_location', '').strip()
        
        print(f"🔍 Search Query - From: {from_location}, To: {to_location}")
        
        # Filter rides based on search criteria
        for ride in sample_rides:
            # Simple matching logic
            from_match = not from_location or from_location.lower() in ride['from_location'].lower()
            to_match = not to_location or to_location.lower() in ride['to_location'].lower()
            
            if from_match and to_match and ride['available_seats'] > 0:
                available_rides.append(ride)
        
        print(f"✅ Found {len(available_rides)} matching rides")
        return render_template('find_ride.html', user=user, available_rides=available_rides)
    
    # GET request - show all rides
    available_rides = [ride for ride in sample_rides if ride['available_seats'] > 0]
    return render_template('find_ride.html', user=user, available_rides=available_rides)

@app.route('/join_ride', methods=['POST'])
@login_required
def join_ride():
    """Join a ride - API endpoint for AJAX calls"""
    user = User(session['user_email'])
    data = request.get_json()
    ride_id = data.get('ride_id')
    
    try:
        ride_id = int(ride_id)
        ride = None
        for r in sample_rides:
            if r['id'] == ride_id:
                ride = r
                break
        
        if ride and ride['available_seats'] > 0:
            ride['available_seats'] -= 1
            print(f"🚗 Ride joined - User: {user.name}, Ride: {ride_id}")
            return jsonify({
                'success': True, 
                'message': f'Successfully joined ride with {ride["driver_name"]}!'
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Sorry, this ride is no longer available.'
            })
    except Exception as e:
        print(f"❌ Join ride error: {e}")
        return jsonify({
            'success': False, 
            'message': 'An error occurred while joining the ride.'
        })

@app.route('/create_ride', methods=['GET', 'POST'])
@login_required
def create_ride():
    """Enhanced ride creation with comprehensive validation"""
    user = User(session['user_email'])
    
    if request.method == 'POST':
        from_location = request.form.get('from_location', '').strip()
        to_location = request.form.get('to_location', '').strip()
        departure_date = request.form.get('departure_date', '')
        departure_time = request.form.get('departure_time', '')
        available_seats = request.form.get('available_seats', 1)
        price_per_seat = request.form.get('price_per_seat', 0)
        car_model = request.form.get('car_model', '').strip()
        additional_info = request.form.get('additional_info', '').strip()
        
        # Comprehensive validation
        if not all([from_location, to_location, departure_date, departure_time]):
            flash('Please fill all required fields (From, To, Date, Time).', 'error')
            return render_template('create_ride.html', user=user)
        
        try:
            available_seats = int(available_seats)
            price_per_seat = float(price_per_seat)
        except (ValueError, TypeError):
            flash('Please enter valid numbers for seats and price.', 'error')
            return render_template('create_ride.html', user=user)
        
        if available_seats < 1 or available_seats > 7:
            flash('Available seats must be between 1 and 7.', 'error')
            return render_template('create_ride.html', user=user)
        
        if price_per_seat < 0:
            flash('Price cannot be negative.', 'error')
            return render_template('create_ride.html', user=user)
        
        # Date validation
        try:
            ride_date = datetime.strptime(departure_date, '%Y-%m-%d').date()
            today = datetime.now().date()
            if ride_date < today:
                flash('Departure date cannot be in the past.', 'error')
                return render_template('create_ride.html', user=user)
        except ValueError:
            flash('Please enter a valid date.', 'error')
            return render_template('create_ride.html', user=user)
        
        # Time formatting
        try:
            time_obj = datetime.strptime(departure_time, '%H:%M')
            formatted_time = time_obj.strftime('%I:%M %p')
        except ValueError:
            flash('Please enter a valid time in HH:MM format.', 'error')
            return render_template('create_ride.html', user=user)
        
        # Create new ride
        new_ride = {
            'id': max([ride['id'] for ride in sample_rides], default=0) + 1,
            'driver_name': user.name,
            'driver_email': user.email,
            'from_location': from_location,
            'to_location': to_location,
            'departure_time': formatted_time,
            'date': departure_date,
            'available_seats': available_seats,
            'total_seats': available_seats,
            'car_model': car_model if car_model else 'Not specified',
            'price_per_seat': price_per_seat,
            'department': user.department if user.department else 'Not specified',
            'year': f"{user.year}{'st' if user.year == 1 else 'nd' if user.year == 2 else 'rd' if user.year == 3 else 'th'} Year",
            'rating': 4.0,
            'phone': user.phone,
            'additional_info': additional_info
        }
        
        sample_rides.append(new_ride)
        print(f"✅ New ride created - ID: {new_ride['id']}, Driver: {user.name}")
        flash(f'Ride created successfully! From {from_location} to {to_location} on {departure_date}', 'success')
        return redirect(url_for('my_rides'))
    
    return render_template('create_ride.html', user=user)

@app.route('/my_rides')
@login_required
def my_rides():
    """Display user's created rides"""
    user = User(session['user_email'])
    user_rides = [ride for ride in sample_rides if ride['driver_email'] == user.email]
    user_rides.sort(key=lambda x: (x['date'], x['departure_time']))
    return render_template('my_rides.html', user=user, rides=user_rides)

@app.route('/delete_ride/<int:ride_id>')
@login_required
def delete_ride(ride_id):
    """Delete a user's ride with enhanced security"""
    user = User(session['user_email'])
    global sample_rides
    
    # Find and verify ownership
    ride_to_delete = None
    for ride in sample_rides:
        if ride['id'] == ride_id and ride['driver_email'] == user.email:
            ride_to_delete = ride
            break
    
    if ride_to_delete:
        original_count = len(sample_rides)
        sample_rides = [ride for ride in sample_rides if ride['id'] != ride_id]
        
        if len(sample_rides) < original_count:
            print(f"🗑️ Ride deleted - ID: {ride_id}, Driver: {user.name}")
            flash('Ride deleted successfully!', 'success')
        else:
            flash('Error deleting ride. Please try again.', 'error')
    else:
        flash('Ride not found or you do not have permission to delete it.', 'error')
    
    return redirect(url_for('my_rides'))

# Enhanced Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    """Enhanced 404 error handler"""
    return f'<h1>404 - Page Not Found</h1><p>Go back to <a href="{url_for("dashboard")}">Dashboard</a></p>', 404

@app.errorhandler(500)
def internal_server_error(e):
    """Enhanced 500 error handler"""
    return f'<h1>500 - Internal Server Error</h1><p>Something went wrong. Go back to <a href="{url_for("dashboard")}">Dashboard</a></p>', 500

@app.errorhandler(413)
def file_too_large(e):
    """Handle file upload size errors"""
    flash('File too large. Please upload an image smaller than 16MB.', 'error')
    return redirect(url_for('edit_profile'))

# DEBUG Routes for Profile Picture Testing
@app.route('/debug/profile')
@login_required
def debug_profile():
    """Debug profile picture issues"""
    user = User(session['user_email'])
    upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'profile_pics')
    
    debug_info = {
        'user_email': user.email,
        'profile_pic': user.profile_pic,
        'upload_folder_exists': os.path.exists(upload_folder),
        'upload_folder_path': upload_folder,
        'app_root_path': app.root_path,
    }
    
    if user.profile_pic:
        pic_path = os.path.join(upload_folder, user.profile_pic)
        debug_info['pic_file_exists'] = os.path.exists(pic_path)
        debug_info['pic_full_path'] = pic_path
        debug_info['pic_url'] = url_for('static', filename=f'uploads/profile_pics/{user.profile_pic}')
        if os.path.exists(pic_path):
            debug_info['pic_file_size'] = os.path.getsize(pic_path)
    
    if os.path.exists(upload_folder):
        debug_info['files_in_folder'] = os.listdir(upload_folder)
    
    debug_html = f"""
    <h2>Profile Picture Debug Info</h2>
    <pre style="background: #f4f4f4; padding: 15px; font-family: monospace;">
{str(debug_info)}
    </pre>
    <h3>User Database Info</h3>
    <pre style="background: #f4f4f4; padding: 15px; font-family: monospace;">
{str(users_db.get(user.email, {}))}
    </pre>
    <a href="{url_for('profile')}">Back to Profile</a>
    """
    return debug_html

# Main execution with enhanced configuration
if __name__ == '__main__':
    print("="*60)
    print("🚗 LIFTLINK CARPOOL - GOOGLE MAPS EDITION")
    print("="*60)
    print("Local URL: http://127.0.0.1:5000")
    print("Network URL: http://localhost:5000")
    print("Xavier's Institute of Engineering")
    print("Sustainable Commute Hub - Google Maps Integration")
    print("="*60)
    print("Features Available:")
    print("✅ User Registration & Secure Login")
    print("✅ Enhanced Find & Search Rides with Google Maps")
    print("✅ Create New Rides with Validation")
    print("✅ My Rides Management")
    print("✅ Complete Profile Management")
    print("✅ FIXED Profile Picture Upload & Display")
    print("✅ Google Maps Route Display")
    print("✅ Mobile Responsive Design")
    print("✅ Smart Route Matching")
    print(f"✅ Sample Routes: {len(sample_rides)} rides loaded")
    print(f"✅ Test Users: {len(users_db)} users available")
    print("="*60)
    print("Test Login Credentials:")
    print("Email: test@student.xavier.ac.in")
    print("Password: password123")
    print("="*60)
    print("Debug URLs:")
    print("Profile Debug: http://127.0.0.1:5000/debug/profile")
    print("="*60)
    print(f"Upload Folder: {UPLOAD_FOLDER}")
    print(f"Upload Folder Exists: {os.path.exists(UPLOAD_FOLDER)}")
    print(f"PIL Available: {PIL_AVAILABLE}")
    print("="*60)
    
    # Enhanced Spyder detection and compatibility
    spyder_detected = False
    if 'runfile' in dir() or 'get_ipython' in globals():
        spyder_detected = True
        print("🔧 Detected Spyder/IPython - Using compatible mode")
    
    try:
        if spyder_detected:
            # Spyder-optimized configuration
            app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True, threaded=True)
        else:
            # Standard configuration for command line
            app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        print(f"❌ Server startup error: {e}")
        print("🔄 Fallback mode activated...")
        try:
            app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False, threaded=True)
        except Exception as fallback_error:
            print(f"❌ Fallback failed: {fallback_error}")
            print("🔧 Manual startup required:")
            print("1. Open Command Prompt")
            print("2. cd to your project folder") 
            print("3. python main.py")
