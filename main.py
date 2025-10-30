from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import json
import hashlib
import os
from datetime import datetime, timedelta
import secrets
import string
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'xie_liftlink_secret_key_2025_dark_theme')

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your_email@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your_app_password')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME', 'your_email@gmail.com')

mail = Mail(app)

# File paths
USERS_FILE = 'users_db.json'
RIDES_FILE = 'rides_db.json'
BOOKINGS_FILE = 'bookings_db.json'
EARNINGS_FILE = 'earnings_db.json'
VERIFICATION_FILE = 'verification_tokens.json'

# Initialize files if they don't exist
def init_files():
    for file_path in [USERS_FILE, RIDES_FILE, BOOKINGS_FILE, EARNINGS_FILE, VERIFICATION_FILE]:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump({}, f)

init_files()

def load_data(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token():
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

def send_verification_email(email, token, name):
    verification_url = url_for('verify_email', token=token, _external=True)
    
    msg = Message(
        subject='🔒 LiftLink Email Verification - Xavier Institute',
        recipients=[email]
    )
    
    msg.html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #1a1a2e; border-radius: 15px; padding: 40px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); color: white; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ font-size: 2.5rem; font-weight: bold; color: #667eea; margin-bottom: 10px; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }}
            .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 20px 0; transition: all 0.3s ease; }}
            .button:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4); }}
            .footer {{ text-align: center; margin-top: 30px; color: #8892b0; font-size: 0.9rem; }}
            .dark-card {{ background: rgba(255,255,255,0.1); border-radius: 10px; padding: 20px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🚗 LiftLink</div>
                <h2 style="color: #8892b0;">Xavier Institute of Engineering</h2>
            </div>
            
            <h3>Hello {name}! 👋</h3>
            
            <p>Welcome to <strong style="color: #667eea;">LiftLink</strong> - Xavier Institute's exclusive dark-themed carpooling platform!</p>
            
            <div class="dark-card">
                <p>To complete your registration and access the premium dark interface, please verify your institutional email address by clicking the button below:</p>
            
                <div style="text-align: center;">
                    <a href="{verification_url}" class="button">
                        ✅ Verify & Enter Dark Mode
                    </a>
                </div>
            </div>
            
            <p><strong>🛡️ Security Features:</strong></p>
            <ul style="color: #8892b0;">
                <li>🔒 This link is valid for 24 hours only</li>
                <li>🏫 Only Xavier Institute email addresses are accepted</li>
                <li>🌙 Access to premium dark theme interface</li>
                <li>🚫 Do not share this link with anyone else</li>
            </ul>
            
            <p>If you didn't request this verification, please ignore this email.</p>
            
            <div class="footer">
                <p>This is an automated message from LiftLink Dark Mode System</p>
                <p>Xavier Institute of Engineering - Smart Campus Initiative</p>
                <p style="color: #667eea;">🌙 Dark Theme • Premium Experience</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

def validate_institutional_email(email):
    """Validate Xavier Institute email domains"""
    valid_domains = ['@student.xavier.ac.in', '@xavier.ac.in']
    return any(email.endswith(domain) for domain in valid_domains)

# Enhanced user database with dark theme styling
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
        'about': 'Final year ETC student interested in sustainable transportation with dark mode UI.',
        'profile_pic': None,
        'verified': True
    },
    '2023032002.durvesh.vsb@student.xavier.ac.in': {
        'name': 'Durvesh Bedre',
        'email': '2023032002.durvesh.vsb@student.xavier.ac.in',
        'password': hashlib.sha256('password123'.encode()).hexdigest(),
        'phone': '7700090035',
        'student_id': '2023032002',
        'department': 'Electronics & Telecommunication',
        'year': 4,
        'gender': 'Male',
        'about': 'Final year ETC student interested in sustainable transportation and premium dark UI experience.',
        'profile_pic': None,
        'verified': True
    }
}

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Enhanced login with dark theme - NO CAPTCHA"""
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('❌ Please fill in all fields!', 'error')
            return render_template('login.html')
        
        # Validate institutional email
        if not validate_institutional_email(email):
            flash('❌ Please use your Xavier Institute email address!', 'error')
            return render_template('login.html')
        
        users = load_data(USERS_FILE)
        user = users.get(email)
        
        if not user:
            flash('❌ Account not found! Please register first.', 'error')
            return render_template('login.html')
        
        if not user.get('verified', False):
            flash('❌ Please verify your email first! Check your inbox.', 'error')
            return render_template('login.html')
        
        if user['password'] == hash_password(password):
            session['user_id'] = email
            session['user_name'] = user['name']
            flash(f'🌙 Welcome back to Dark Mode, {user["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('❌ Invalid password!', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Enhanced registration with dark theme styling"""
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone = request.form.get('phone', '').strip()
        user_type = request.form.get('user_type', '')
        department = request.form.get('department', '').strip()
        year = request.form.get('year', '').strip()
        designation = request.form.get('designation', '').strip()
        emergency_name = request.form.get('emergency_name', '').strip()
        emergency_phone = request.form.get('emergency_phone', '').strip()
        
        # Validation
        if not all([name, email, password, confirm_password, phone, user_type, emergency_name, emergency_phone]):
            flash('❌ Please fill in all required fields!', 'error')
            return render_template('register.html')
        
        if not validate_institutional_email(email):
            flash('❌ Please use your Xavier Institute email address!', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('❌ Passwords do not match!', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('❌ Password must be at least 6 characters!', 'error')
            return render_template('register.html')
        
        users = load_data(USERS_FILE)
        
        if email in users:
            flash('❌ Email already registered!', 'error')
            return render_template('register.html')
        
        # Generate verification token
        token = generate_token()
        verification_tokens = load_data(VERIFICATION_FILE)
        
        # Store verification token (expires in 24 hours)
        verification_tokens[token] = {
            'email': email,
            'expires': (datetime.now() + timedelta(hours=24)).isoformat(),
            'user_data': {
                'name': name,
                'email': email,
                'password': hash_password(password),
                'phone': phone,
                'user_type': user_type,
                'department': department if user_type == 'student' else '',
                'year': year if user_type == 'student' else '',
                'designation': designation if user_type == 'staff' else '',
                'emergency_contact': {
                    'name': emergency_name,
                    'phone': emergency_phone
                },
                'verified': False,
                'created_at': datetime.now().isoformat(),
                'profile_pic': None,
                'about': f'Xavier Institute {user_type} interested in sustainable carpooling with dark mode UI.'
            }
        }
        
        save_data(VERIFICATION_FILE, verification_tokens)
        
        # Send verification email
        if send_verification_email(email, token, name):
            flash('✅ Registration initiated! Please check your email to verify your account and access dark mode.', 'success')
            return render_template('verification_sent.html', email=email)
        else:
            flash('❌ Failed to send verification email. Please try again.', 'error')
    
    return render_template('register.html')

@app.route('/verify_email/<token>')
def verify_email(token):
    """Email verification with dark theme welcome"""
    verification_tokens = load_data(VERIFICATION_FILE)
    
    if token not in verification_tokens:
        flash('❌ Invalid verification link!', 'error')
        return redirect(url_for('login'))
    
    token_data = verification_tokens[token]
    
    # Check if token expired
    if datetime.now() > datetime.fromisoformat(token_data['expires']):
        # Clean up expired token
        del verification_tokens[token]
        save_data(VERIFICATION_FILE, verification_tokens)
        flash('❌ Verification link has expired! Please register again.', 'error')
        return redirect(url_for('register'))
    
    # Verify user
    users = load_data(USERS_FILE)
    user_data = token_data['user_data']
    user_data['verified'] = True
    
    users[user_data['email']] = user_data
    save_data(USERS_FILE, users)
    
    # Clean up verification token
    del verification_tokens[token]
    save_data(VERIFICATION_FILE, verification_tokens)
    
    flash('🌙 Email verified successfully! Welcome to LiftLink Dark Mode. You can now login.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Enhanced dashboard with dark theme"""
    if 'user_id' not in session:
        flash('❌ Please login first!', 'error')
        return redirect(url_for('login'))
    
    user_email = session['user_id']
    users = load_data(USERS_FILE)
    rides = load_data(RIDES_FILE)
    bookings = load_data(BOOKINGS_FILE)
    earnings = load_data(EARNINGS_FILE)
    
    user = users.get(user_email, {})
    
    # Get user's created rides
    user_rides = [ride for ride in rides.values() if ride.get('driver') == user_email]
    
    # Get user's bookings
    user_bookings = [booking for booking in bookings.values() if booking.get('passenger') == user_email]
    
    # Get earnings
    user_earnings = earnings.get(user_email, [])
    total_earnings = sum(float(earning.get('amount', 0)) for earning in user_earnings)
    
    return render_template('dashboard.html', 
                         user=user,
                         user_rides=user_rides,
                         user_bookings=user_bookings,
                         user_earnings=user_earnings,
                         total_earnings=total_earnings)

@app.route('/create_ride', methods=['GET', 'POST'])
def create_ride():
    """Enhanced ride creation with dark theme"""
    if 'user_id' not in session:
        flash('❌ Please login first!', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        from_location = request.form.get('from_location', '').strip()
        to_location = request.form.get('to_location', '').strip()
        date = request.form.get('date', '')
        time = request.form.get('time', '')
        seats = request.form.get('seats', '')
        price = request.form.get('price', '')
        car_model = request.form.get('car_model', '').strip()
        car_number = request.form.get('car_number', '').strip().upper()
        notes = request.form.get('notes', '').strip()
        
        # Validation
        if not all([from_location, to_location, date, time, seats, price]):
            flash('❌ Please fill in all required fields!', 'error')
            return render_template('create_ride.html')
        
        try:
            seats = int(seats)
            price = float(price)
            if seats <= 0 or price <= 0:
                raise ValueError
        except ValueError:
            flash('❌ Please enter valid seats and price!', 'error')
            return render_template('create_ride.html')
        
        # Create ride ID
        ride_id = datetime.now().strftime('%Y%m%d%H%M%S') + '_' + session['user_id'].split('@')[0]
        
        rides = load_data(RIDES_FILE)
        
        rides[ride_id] = {
            'id': ride_id,
            'driver': session['user_id'],
            'driver_name': session['user_name'],
            'from_location': from_location,
            'to_location': to_location,
            'date': date,
            'time': time,
            'total_seats': seats,
            'available_seats': seats,
            'price': price,
            'car_model': car_model,
            'car_number': car_number,
            'notes': notes,
            'created_at': datetime.now().isoformat()
        }
        
        save_data(RIDES_FILE, rides)
        flash('🌙 Ride created successfully in dark mode!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('create_ride.html')

@app.route('/find_ride')
def find_ride():
    """Enhanced ride finding with dark theme"""
    if 'user_id' not in session:
        flash('❌ Please login first!', 'error')
        return redirect(url_for('login'))
    
    # Get search parameters
    search_from = request.args.get('from_location', '').strip()
    search_to = request.args.get('to_location', '').strip()
    search_date = request.args.get('date', '')
    
    rides = load_data(RIDES_FILE)
    bookings = load_data(BOOKINGS_FILE)
    users = load_data(USERS_FILE)
    
    current_user = session['user_id']
    available_rides = []
    
    # Get user's bookings to check booking status
    user_bookings = {booking['ride_id']: booking for booking in bookings.values() 
                    if booking.get('passenger') == current_user}
    
    for ride_id, ride in rides.items():
        # Don't show user's own rides
        if ride.get('driver') == current_user:
            continue
        
        # Only show rides with available seats
        if ride.get('available_seats', 0) <= 0:
            continue
        
        # Filter by search criteria if provided
        match_from = not search_from or search_from.lower() in ride.get('from_location', '').lower()
        match_to = not search_to or search_to.lower() in ride.get('to_location', '').lower()
        match_date = not search_date or search_date == ride.get('date', '')
        
        if match_from and match_to and match_date:
            # Get driver info
            driver_info = users.get(ride.get('driver'), {})
            ride['driver_phone'] = driver_info.get('phone', '')
            
            # Check if user has already booked this ride
            ride['user_booked'] = ride_id in user_bookings
            
            available_rides.append(ride)
    
    return render_template('find_ride.html', 
                         rides=available_rides,
                         search_from=search_from,
                         search_to=search_to,
                         search_date=search_date)

@app.route('/book_ride/<ride_id>')
def book_ride(ride_id):
    """Enhanced ride booking with dark theme"""
    if 'user_id' not in session:
        flash('❌ Please login first!', 'error')
        return redirect(url_for('login'))
    
    user_email = session['user_id']
    rides = load_data(RIDES_FILE)
    bookings = load_data(BOOKINGS_FILE)
    earnings = load_data(EARNINGS_FILE)
    users = load_data(USERS_FILE)
    
    # Check if ride exists
    if ride_id not in rides:
        flash('❌ Ride not found!', 'error')
        return redirect(url_for('find_ride'))
    
    ride = rides[ride_id]
    
    # Check if user is trying to book their own ride
    if ride.get('driver') == user_email:
        flash('❌ You cannot book your own ride!', 'error')
        return redirect(url_for('find_ride'))
    
    # Check if user has already booked this ride
    user_bookings = [booking for booking in bookings.values() 
                    if booking.get('passenger') == user_email and booking.get('ride_id') == ride_id]
    if user_bookings:
        flash('❌ You have already booked this ride! Only one seat per ride allowed.', 'error')
        return redirect(url_for('find_ride'))
    
    # Check seat availability
    if ride.get('available_seats', 0) <= 0:
        flash('❌ No seats available for this ride!', 'error')
        return redirect(url_for('find_ride'))
    
    # Create booking
    booking_id = datetime.now().strftime('%Y%m%d%H%M%S') + '_' + user_email.split('@')[0]
    
    bookings[booking_id] = {
        'id': booking_id,
        'ride_id': ride_id,
        'passenger': user_email,
        'passenger_name': session['user_name'],
        'driver': ride.get('driver'),
        'driver_name': ride.get('driver_name'),
        'from_location': ride.get('from_location'),
        'to_location': ride.get('to_location'),
        'date': ride.get('date'),
        'time': ride.get('time'),
        'price': ride.get('price'),
        'status': 'confirmed',
        'booked_at': datetime.now().isoformat()
    }
    
    # Update ride available seats
    rides[ride_id]['available_seats'] -= 1
    
    # Add to driver's earnings
    driver_email = ride.get('driver')
    if driver_email not in earnings:
        earnings[driver_email] = []
    
    earnings[driver_email].append({
        'passenger_name': session['user_name'],
        'amount': ride.get('price'),
        'route': f"{ride.get('from_location')} → {ride.get('to_location')}",
        'date': ride.get('date'),
        'time': ride.get('time'),
        'booking_date': datetime.now().isoformat()
    })
    
    # Save all data
    save_data(BOOKINGS_FILE, bookings)
    save_data(RIDES_FILE, rides)
    save_data(EARNINGS_FILE, earnings)
    
    flash('🌙 Ride booked successfully in dark mode!', 'success')
    return redirect(url_for('find_ride'))

@app.route('/my_rides')
def my_rides():
    """Enhanced my rides with dark theme"""
    if 'user_id' not in session:
        flash('❌ Please login first!', 'error')
        return redirect(url_for('login'))
    
    user_email = session['user_id']
    rides = load_data(RIDES_FILE)
    bookings = load_data(BOOKINGS_FILE)
    
    # Get user's created rides
    user_rides = [ride for ride in rides.values() if ride.get('driver') == user_email]
    
    # Get user's bookings
    user_bookings = [booking for booking in bookings.values() if booking.get('passenger') == user_email]
    
    return render_template('my_rides.html', 
                         user_rides=user_rides,
                         user_bookings=user_bookings)

@app.route('/profile')
def profile():
    """Enhanced profile with dark theme"""
    if 'user_id' not in session:
        flash('❌ Please login first!', 'error')
        return redirect(url_for('login'))
    
    users = load_data(USERS_FILE)
    user = users.get(session['user_id'], {})
    
    return render_template('profile.html', user=user)

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    """Enhanced profile editing with dark theme"""
    if 'user_id' not in session:
        flash('❌ Please login first!', 'error')
        return redirect(url_for('login'))
    
    users = load_data(USERS_FILE)
    user_email = session['user_id']
    
    if request.method == 'POST':
        # Update user data
        users[user_email]['name'] = request.form.get('name', '').strip()
        users[user_email]['phone'] = request.form.get('phone', '').strip()
        users[user_email]['department'] = request.form.get('department', '').strip()
        users[user_email]['year'] = request.form.get('year', '').strip()
        users[user_email]['designation'] = request.form.get('designation', '').strip()
        users[user_email]['about'] = request.form.get('about', '').strip()
        users[user_email]['emergency_contact']['name'] = request.form.get('emergency_name', '').strip()
        users[user_email]['emergency_contact']['phone'] = request.form.get('emergency_phone', '').strip()
        
        # Update session name if changed
        session['user_name'] = users[user_email]['name']
        
        save_data(USERS_FILE, users)
        flash('🌙 Profile updated successfully in dark mode!', 'success')
        return redirect(url_for('profile'))
    
    user = users.get(user_email, {})
    return render_template('edit_profile.html', user=user)

@app.route('/earnings')
def earnings():
    """Enhanced earnings with dark theme"""
    if 'user_id' not in session:
        flash('❌ Please login first!', 'error')
        return redirect(url_for('login'))
    
    user_email = session['user_id']
    earnings_data = load_data(EARNINGS_FILE)
    
    user_earnings = earnings_data.get(user_email, [])
    total_earnings = sum(float(earning.get('amount', 0)) for earning in user_earnings)
    
    return render_template('earnings.html', 
                         earnings=user_earnings,
                         total_earnings=total_earnings)

@app.route('/logout')
def logout():
    """Enhanced logout with dark theme"""
    session.clear()
    flash('🌙 Logged out successfully from dark mode!', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌙 LIFTLINK DARK MODE - EMAIL VERIFICATION (NO CAPTCHA)")
    print("="*60)
    print("📍 Local URL: http://127.0.0.1:5000")
    print("📍 Network URL: http://localhost:5000")
    print("🎯 Xavier's Institute of Engineering")
    print("🌟 Premium Dark Theme Carpool Hub")
    print("="*60)
    print("✅ Features Available:")
    print("   - 🌙 Premium Dark Theme UI")
    print("   - 📧 Email Verification System")
    print("   - 🔐 Secure User Registration & Login")
    print("   - 🚫 NO CAPTCHA (Removed)")
    print("   - 🔍 Enhanced Find & Search Rides")
    print("   - ➕ Create New Rides with Dark UI")
    print("   - 🚗 My Rides Management")
    print("   - 👤 Complete Profile Management")
    print("   - 💰 Earnings Tracking")
    print("   - 📱 Mobile Responsive Dark Design")
    print("="*60)
    print("🔑 Test Login Credentials:")
    print("   📧 Email: test@student.xavier.ac.in")
    print("   🔒 Password: password123")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
