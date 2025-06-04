from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import sqlite3
import hashlib
import datetime
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key-123'

# Database initialization
def init_db():
    conn = sqlite3.connect('cab_booking.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        pickup_location TEXT,
        dropoff_location TEXT,
        pickup_time TEXT,
        status TEXT,
        driver_id INTEGER,
        fare REAL,
        FOREIGN KEY(employee_id) REFERENCES employees(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        vehicle TEXT,
        status TEXT
    )''')
    # Insert sample drivers
    c.execute("INSERT OR IGNORE INTO drivers (name, vehicle, status) VALUES (?, ?, ?)", 
             ('John Doe', 'Toyota Camry', 'available'))
    c.execute("INSERT OR IGNORE INTO drivers (name, vehicle, status) VALUES (?, ?, ?)", 
             ('Jane Smith', 'Honda Accord', 'available'))
    conn.commit()
    conn.close()

# Home route
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        conn = sqlite3.connect('cab_booking.db')
        c = conn.cursor()
        c.execute("SELECT * FROM employees WHERE username = ? AND password = ?", 
                 (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['name'] = user[3]
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid credentials'})
    return render_template('login.html')

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        name = request.form['name']
        conn = sqlite3.connect('cab_booking.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO employees (username, password, name) VALUES (?, ?, ?)",
                     (username, password, name))
            conn.commit()
            return jsonify({'success': True})
        except sqlite3.IntegrityError:
            return jsonify({'success': False, 'message': 'Username already exists'})
        finally:
            conn.close()
    return render_template('register.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('name', None)
    return redirect(url_for('login'))

# Book cab route
@app.route('/book', methods=['POST'])
def book_cab():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login'})
    
    data = request.get_json()
    pickup = data['pickup']
    dropoff = data['dropoff']
    pickup_time = data['pickup_time']
    
    # Simple fare estimation (distance-based, simulated)
    distance = random.uniform(5, 20)  # Simulated distance in km
    fare = round(distance * 2.5, 2)  # $2.5 per km
    
    conn = sqlite3.connect('cab_booking.db')
    c = conn.cursor()
    
    # Find available driver
    c.execute("SELECT id FROM drivers WHERE status = 'available' LIMIT 1")
    driver = c.fetchone()
    
    if not driver:
        conn.close()
        return jsonify({'success': False, 'message': 'No drivers available'})
    
    driver_id = driver[0]
    
    # Create booking
    c.execute("INSERT INTO bookings (employee_id, pickup_location, dropoff_location, pickup_time, status, driver_id, fare) VALUES (?, ?, ?, ?, ?, ?, ?)",
             (session['user_id'], pickup, dropoff, pickup_time, 'booked', driver_id, fare))
    
    # Update driver status
    c.execute("UPDATE drivers SET status = 'busy' WHERE id = ?", (driver_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Cab booked successfully',
        'fare': fare,
        'driver_id': driver_id
    })

# Get bookings
@app.route('/bookings')
def get_bookings():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login'})
    
    conn = sqlite3.connect('cab_booking.db')
    c = conn.cursor()
    c.execute("SELECT b.id, b.pickup_location, b.dropoff_location, b.pickup_time, b.status, b.fare, d.name as driver_name, d.vehicle FROM bookings b JOIN drivers d ON b.driver_id = d.id WHERE b.employee_id = ?", (session['user_id'],))
    bookings = [{'id': row[0], 'pickup': row[1], 'dropoff': row[2], 'pickup_time': row[3], 
                'status': row[4], 'fare': row[5], 'driver_name': row[6], 'vehicle': row[7]} 
               for row in c.fetchall()]
    conn.close()
    return jsonify(bookings)

# Simulated real-time tracking
@app.route('/track/<int:booking_id>')
def track_booking(booking_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login'})
    
    # Simulated coordinates (in a real app, this would come from driver's GPS)
    progress = random.uniform(0, 100)
    status = 'in_progress' if progress < 100 else 'completed'
    
    return jsonify({
        'success': True,
        'booking_id': booking_id,
        'progress': progress,
        'status': status,
        'coordinates': {
            'lat': random.uniform(40.7, 40.8),  # Simulated NYC coordinates
            'lng': random.uniform(-74.0, -73.9)
        }
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)