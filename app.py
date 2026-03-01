from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import mysql.connector
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from decimal import Decimal


def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimal(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)  # or str(obj) if precision matters
    return obj


# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
# Database connection function
def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    return connection

# Helper function to execute query and fetch results
def execute_query(query, params=None, fetchone=False, commit=False):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True, buffered=True)
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        if commit:
            connection.commit()
            return cursor.lastrowid
        
        if fetchone:
            return cursor.fetchone()
        else:
            return cursor.fetchall()
    except Exception as e:
        print(f"Database error: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

# Login required decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Routes

@app.route('/')
def index():
    if 'user_id' in session:
        # Get dashboard data
        total_rooms = execute_query("SELECT COUNT(*) as count FROM rooms", fetchone=True)
        available_rooms = execute_query("SELECT COUNT(*) as count FROM rooms WHERE status = 'Available'", fetchone=True)
        today_checkins = execute_query(
            "SELECT COUNT(*) as count FROM reservations WHERE check_in = CURDATE() AND status = 'confirmed'", 
            fetchone=True
        )
        today_checkouts = execute_query(
            "SELECT COUNT(*) as count FROM reservations WHERE check_out = CURDATE() AND status = 'checked_in'", 
            fetchone=True
        )
        
        # Get recent reservations
        recent_reservations = execute_query(
            """SELECT r.id, r.guest_name, r.check_in, r.check_out, r.status, ro.room_number 
               FROM reservations r 
               JOIN rooms ro ON r.room_id = ro.id 
               ORDER BY r.created_at DESC LIMIT 5"""
        )
        
        return render_template('index.html', 
                               total_rooms=total_rooms['count'], 
                               available_rooms=available_rooms['count'],
                               today_checkins=today_checkins['count'],
                               today_checkouts=today_checkouts['count'],
                               recent_reservations=recent_reservations)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = execute_query("SELECT * FROM users WHERE email = %s", (email,), fetchone=True)
        
        if user and user['password'] == password:  # In production, use check_password_hash
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Rooms
@app.route('/rooms')
@login_required
def rooms():
    all_rooms = execute_query("SELECT * FROM rooms ORDER BY room_number")
    
    def convert_decimal(obj):
        if isinstance(obj, list):
            return [convert_decimal(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: convert_decimal(value) for key, value in obj.items()}
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj

    converted_rooms = convert_decimal(all_rooms)
    return render_template('rooms.html', rooms=converted_rooms)

@app.route('/rooms/add', methods=['POST'])
@login_required
def add_room():
    if request.method == 'POST':
        room_number = request.form['room_number']
        room_type = request.form['room_type']
        capacity = request.form['capacity']
        price = request.form['price']
        amenities = json.dumps({
            "wifi": "wifi" in request.form,
            "tv": "tv" in request.form,
            "ac": "ac" in request.form,
            "minibar": "minibar" in request.form,
            "jacuzzi": "jacuzzi" in request.form,
            "balcony": "balcony" in request.form
        })
        
        execute_query(
            """INSERT INTO rooms (room_number, room_type, capacity, price, amenities, status) 
               VALUES (%s, %s, %s, %s, %s, 'Available')""",
            (room_number, room_type, capacity, price, amenities),
            commit=True
        )
        
        flash('Room added successfully', 'success')
        return redirect(url_for('rooms'))

@app.route('/rooms/get/<int:id>')
@login_required
def get_room(id):
    try:
        room = execute_query(
            "SELECT * FROM rooms WHERE id = %s",
            (id,),
            fetchone=True
        )
        
        if not room:
            return jsonify({'error': 'Room not found'}), 404
        
        # Convert Decimal to float
        room['price'] = float(room['price'])
        room['capacity'] = int(room['capacity'])
        
        return jsonify(room)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/rooms/update/<int:id>', methods=['POST'])
@login_required
def update_room(id):
    if request.method == 'POST':
        try:
            room_type = request.form['room_type']
            capacity = request.form['capacity']
            price = request.form['price']
            status = request.form['status']
            amenities = json.dumps({
                "wifi": "wifi" in request.form,
                "tv": "tv" in request.form,
                "ac": "ac" in request.form,
                "minibar": "minibar" in request.form,
                "jacuzzi": "jacuzzi" in request.form,
                "balcony": "balcony" in request.form
            })
            
            execute_query(
                """UPDATE rooms SET room_type = %s, capacity = %s, price = %s, 
                   amenities = %s, status = %s WHERE id = %s""",
                (room_type, capacity, price, amenities, status, id),
                commit=True
            )
            
            # Get updated room data
            updated_room = execute_query(
                "SELECT * FROM rooms WHERE id = %s",
                (id,),
                fetchone=True
            )
            
            # Convert Decimal to float
            if updated_room:
                updated_room['price'] = float(updated_room['price'])
                updated_room['capacity'] = int(updated_room['capacity'])
            
            return jsonify({
                'message': 'Room updated successfully',
                'room': updated_room
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Reservations
@app.route('/reservations')
@login_required
def reservations():
    all_reservations = execute_query(
        """SELECT r.*, rm.room_number, rm.room_type 
           FROM reservations r 
           JOIN rooms rm ON r.room_id = rm.id 
           ORDER BY r.check_in DESC"""
    )
    
    all_rooms = execute_query(
        "SELECT id, room_number, room_type, capacity FROM rooms WHERE status = 'Available'"
    )

    # Convert Decimals to float to avoid serialization error
    all_reservations = convert_decimal(all_reservations)
    all_rooms = convert_decimal(all_rooms)
    
    return render_template('reservations.html', reservations=all_reservations, rooms=all_rooms)


@app.route('/reservations/add', methods=['POST'])
@login_required
def add_reservation():
    if request.method == 'POST':
        room_id = request.form['room_id']
        guest_name = request.form['guest_name']
        guest_email = request.form['guest_email']
        guest_phone = request.form['guest_phone']
        check_in = request.form['check_in']
        check_out = request.form['check_out']
        adults = request.form['adults']
        children = request.form.get('children', 0)
        status = 'confirmed'
        payment_status = request.form['payment_status']
        payment_amount = request.form['payment_amount']
        
        # Check for overlapping reservations (prevent double-booking)
        conflict = execute_query(
            """SELECT id, guest_name, check_in, check_out FROM reservations 
               WHERE room_id = %s 
               AND status NOT IN ('cancelled', 'checked_out')
               AND check_in < %s AND check_out > %s""",
            (room_id, check_out, check_in),
            fetchone=True
        )
        
        if conflict:
            flash(f'Room is already booked from {conflict["check_in"]} to {conflict["check_out"]} by {conflict["guest_name"]}. Please choose different dates or another room.', 'error')
            return redirect(url_for('reservations'))
        
        # Insert reservation
        reservation_id = execute_query(
            """INSERT INTO reservations (room_id, guest_name, guest_email, guest_phone, check_in, check_out, 
               adults, children, status, payment_status, payment_amount) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (room_id, guest_name, guest_email, guest_phone, check_in, check_out, 
             adults, children, status, payment_status, payment_amount),
            commit=True
        )
        
        # Update room status to Occupied if check-in is today
        if check_in == datetime.now().strftime('%Y-%m-%d'):
            execute_query(
                "UPDATE rooms SET status = 'Occupied' WHERE id = %s",
                (room_id,),
                commit=True
            )
        
        flash('Reservation added successfully', 'success')
        return redirect(url_for('reservations'))

@app.route('/reservations/update/<int:id>', methods=['POST'])
@login_required
def update_reservation(id):
    if request.method == 'POST':
        status = request.form['status']
        payment_status = request.form['payment_status']
        
        # Get reservation details
        reservation = execute_query(
            "SELECT room_id, status FROM reservations WHERE id = %s",
            (id,),
            fetchone=True
        )
        
        # Update reservation
        execute_query(
            "UPDATE reservations SET status = %s, payment_status = %s WHERE id = %s",
            (status, payment_status, id),
            commit=True
        )
        
        # Update room status based on reservation status
        if status == 'checked_in' and reservation['status'] != 'checked_in':
            execute_query(
                "UPDATE rooms SET status = 'Occupied' WHERE id = %s",
                (reservation['room_id'],),
                commit=True
            )
        elif status == 'checked_out' and reservation['status'] != 'checked_out':
            execute_query(
                "UPDATE rooms SET status = 'Available' WHERE id = %s",
                (reservation['room_id'],),
                commit=True
            )
        
        flash('Reservation updated successfully', 'success')
        return redirect(url_for('reservations'))

# Services
@app.route('/services')
@login_required
def services():
    all_services = execute_query("SELECT * FROM services")
    all_reservations = execute_query(
        """SELECT r.id, r.guest_name, ro.room_number 
           FROM reservations r 
           JOIN rooms ro ON r.room_id = ro.id 
           WHERE r.status IN ('confirmed', 'checked_in')"""
    )
    service_orders = execute_query(
        """SELECT so.*, s.service_name, s.price, r.guest_name, ro.room_number 
           FROM service_orders so 
           JOIN services s ON so.service_id = s.id 
           JOIN reservations r ON so.reservation_id = r.id 
           JOIN rooms ro ON r.room_id = ro.id 
           ORDER BY so.order_date DESC"""
    )
    
    # Convert Decimal values to float
    for service in all_services:
        service['price'] = float(service['price'])
    
    for order in service_orders:
        order['price'] = float(order['price'])
    
    return render_template('services.html', services=all_services, 
                          reservations=all_reservations, service_orders=service_orders)

@app.route('/services/add', methods=['POST'])
@login_required
def add_service():
    if request.method == 'POST':
        service_name = request.form['service_name']
        description = request.form['description']
        price = request.form['price']
        available = 'available' in request.form
        
        execute_query(
            "INSERT INTO services (service_name, description, price, available) VALUES (%s, %s, %s, %s)",
            (service_name, description, price, available),
            commit=True
        )
        
        flash('Service added successfully', 'success')
        return redirect(url_for('services'))

@app.route('/service_orders/add', methods=['POST'])
@login_required
def add_service_order():
    if request.method == 'POST':
        reservation_id = request.form['reservation_id']
        service_id = request.form['service_id']
        quantity = request.form['quantity']
        notes = request.form['notes']
        
        execute_query(
            """INSERT INTO service_orders (reservation_id, service_id, quantity, notes, status) 
               VALUES (%s, %s, %s, %s, 'pending')""",
            (reservation_id, service_id, quantity, notes),
            commit=True
        )
        
        flash('Service order added successfully', 'success')
        return redirect(url_for('services'))

@app.route('/service_orders/update/<int:id>', methods=['POST'])
@login_required
def update_service_order(id):
    if request.method == 'POST':
        try:
            status = request.form['status']
            
            # Validate status
            valid_statuses = ['pending', 'in progress', 'completed', 'cancelled']
            if status not in valid_statuses:
                return jsonify({'error': 'Invalid status'}), 400
            
            # Update service order status
            execute_query(
                "UPDATE service_orders SET status = %s WHERE id = %s",
                (status, id),
                commit=True
            )
            
            # Get updated order details
            updated_order = execute_query(
                """SELECT so.*, s.service_name, s.price, r.guest_name, ro.room_number 
                   FROM service_orders so 
                   JOIN services s ON so.service_id = s.id 
                   JOIN reservations r ON so.reservation_id = r.id 
                   JOIN rooms ro ON r.room_id = ro.id 
                   WHERE so.id = %s""",
                (id,),
                fetchone=True
            )
            
            # Convert Decimal to float
            if updated_order:
                updated_order['price'] = float(updated_order['price'])
            
            return jsonify({
                'message': 'Service order status updated successfully',
                'order': updated_order
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Housekeeping
@app.route('/housekeeping')
@login_required
def housekeeping():
    rooms_status = execute_query(
        "SELECT id, room_number, status FROM rooms ORDER BY room_number"
    )
    return render_template('housekeeping.html', rooms=rooms_status)

@app.route('/housekeeping/update/<int:id>', methods=['POST'])
@login_required
def update_housekeeping(id):
    if request.method == 'POST':
        status = request.form['status']
        
        execute_query(
            "UPDATE rooms SET status = %s WHERE id = %s",
            (status, id),
            commit=True
        )
        
        flash('Room status updated successfully', 'success')
        return redirect(url_for('housekeeping'))

# Billing
@app.route('/billing')
@login_required
def billing():
    bills = execute_query(
        """SELECT b.*, r.guest_name, r.check_in, r.check_out, ro.room_number 
           FROM bills b 
           JOIN reservations r ON b.reservation_id = r.id 
           JOIN rooms ro ON r.room_id = ro.id 
           ORDER BY b.payment_date DESC"""
    )
    
    reservations = execute_query(
        """SELECT r.id, r.guest_name, ro.room_number, r.check_in, r.check_out, 
              r.payment_amount, r.payment_status 
           FROM reservations r 
           JOIN rooms ro ON r.room_id = ro.id 
           WHERE r.status IN ('confirmed', 'checked_in', 'checked_out') 
           AND (r.id NOT IN (SELECT reservation_id FROM bills WHERE status != 'refunded')
                OR r.payment_status != 'paid')"""
    )
    
    return render_template('billing.html', bills=bills, reservations=reservations)

@app.route('/billing/generate/<int:reservation_id>')
@login_required
def generate_bill(reservation_id):
    try:
        # Get reservation details
        reservation = execute_query(
            """SELECT r.*, ro.price, ro.room_number, ro.room_type 
               FROM reservations r 
               JOIN rooms ro ON r.room_id = ro.id 
               WHERE r.id = %s""",
            (reservation_id,),
            fetchone=True
        )
        
        if not reservation:
            return jsonify({'error': 'Reservation not found'}), 404
        
        # Convert Decimal to float for room price
        room_price = float(reservation['price'])
        
        # Calculate room charge
        check_in = datetime.strptime(str(reservation['check_in']), '%Y-%m-%d')
        check_out = datetime.strptime(str(reservation['check_out']), '%Y-%m-%d')
        days = (check_out - check_in).days
        room_charge = room_price * days
        
        # Get all service orders with their costs
        service_orders = execute_query(
            """SELECT so.id, so.quantity, s.service_name, s.price, so.status,
                  (s.price * so.quantity) as total_cost
               FROM service_orders so 
               JOIN services s ON so.service_id = s.id 
               WHERE so.reservation_id = %s 
               AND so.status IN ('pending', 'in progress', 'completed')""",
            (reservation_id,)
        )
        
        # Convert Decimal to float for service orders
        for order in service_orders:
            order['price'] = float(order['price'])
            order['total_cost'] = float(order['total_cost'])
        
        # Calculate service charges
        service_charge = sum(order['total_cost'] for order in service_orders)
        
        # Calculate total
        total_amount = room_charge + service_charge
        
        # Convert payment_amount to float, default to 0 if None
        paid_amount = float(reservation['payment_amount']) if reservation['payment_amount'] is not None else 0.0
        
        response_data = {
            'reservation': {
                'guest_name': reservation['guest_name'],
                'room_number': reservation['room_number'],
                'check_in': str(reservation['check_in']),
                'check_out': str(reservation['check_out']),
                'days': days,
            },
            'room_charge': round(room_charge, 2),
            'service_orders': service_orders,
            'service_charge': round(service_charge, 2),
            'total_amount': round(total_amount, 2),
            'paid_amount': round(paid_amount, 2),
            'balance': round(total_amount - paid_amount, 2)
        }
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/billing/create', methods=['POST'])
@login_required
def create_bill():
    if request.method == 'POST':
        try:
            reservation_id = request.form['reservation_id']
            total_amount = request.form['total_amount']
            payment_method = request.form['payment_method']
            status = request.form['status']
            
            # Validate required fields
            if not all([reservation_id, total_amount, payment_method, status]):
                flash('All fields are required', 'danger')
                return redirect(url_for('billing'))
            
            # Create bill
            execute_query(
                """INSERT INTO bills (reservation_id, total_amount, payment_method, status) 
                   VALUES (%s, %s, %s, %s)""",
                (reservation_id, total_amount, payment_method, status),
                commit=True
            )
            
            # Update reservation payment status
            if status == 'paid':
                execute_query(
                    "UPDATE reservations SET payment_status = 'paid', payment_amount = %s WHERE id = %s",
                    (total_amount, reservation_id),
                    commit=True
                )
            
            flash('Bill created successfully', 'success')
            return redirect(url_for('billing'))
        except Exception as e:
            flash(f'Error creating bill: {str(e)}', 'danger')
            return redirect(url_for('billing'))

# Feedback
@app.route('/feedback/<int:reservation_id>', methods=['GET', 'POST'])
def feedback(reservation_id):
    if request.method == 'POST':
        rating = request.form['rating']
        comments = request.form['comments']
        
        execute_query(
            "INSERT INTO feedback (reservation_id, rating, comments) VALUES (%s, %s, %s)",
            (reservation_id, rating, comments),
            commit=True
        )
        
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('index'))
    
    reservation = execute_query(
        """SELECT r.id, r.guest_name, ro.room_number 
           FROM reservations r 
           JOIN rooms ro ON r.room_id = ro.id 
           WHERE r.id = %s""",
        (reservation_id,),
        fetchone=True
    )
    
    return render_template('feedback.html', reservation=reservation)

# ==================== NEW FEATURES ====================

# Staff Management
@app.route('/staff')
@login_required
def staff():
    all_staff = execute_query("SELECT * FROM staff ORDER BY name")
    if all_staff:
        all_staff = convert_decimal(all_staff)
    return render_template('staff.html', staff=all_staff or [])

@app.route('/staff/add', methods=['POST'])
@login_required
def add_staff():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        role = request.form['role']
        shift = request.form['shift']
        salary = request.form['salary']
        hire_date = request.form['hire_date']
        
        execute_query(
            """INSERT INTO staff (name, email, phone, role, shift, salary, hire_date) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (name, email, phone, role, shift, salary, hire_date),
            commit=True
        )
        
        # Create notification
        execute_query(
            "INSERT INTO notifications (title, message, type) VALUES (%s, %s, 'info')",
            (f'New Staff Added', f'{name} has been added as {role}.'),
            commit=True
        )
        
        flash('Staff member added successfully', 'success')
        return redirect(url_for('staff'))

@app.route('/staff/update/<int:id>', methods=['POST'])
@login_required
def update_staff(id):
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            role = request.form['role']
            shift = request.form['shift']
            salary = request.form['salary']
            status = request.form['status']
            
            execute_query(
                """UPDATE staff SET name=%s, email=%s, phone=%s, role=%s, 
                   shift=%s, salary=%s, status=%s WHERE id=%s""",
                (name, email, phone, role, shift, salary, status, id),
                commit=True
            )
            
            return jsonify({'message': 'Staff updated successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/staff/get/<int:id>')
@login_required
def get_staff(id):
    try:
        member = execute_query("SELECT * FROM staff WHERE id = %s", (id,), fetchone=True)
        if not member:
            return jsonify({'error': 'Staff member not found'}), 404
        member = convert_decimal(member)
        member['hire_date'] = str(member['hire_date'])
        return jsonify(member)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/staff/delete/<int:id>', methods=['POST'])
@login_required
def delete_staff(id):
    execute_query("DELETE FROM staff WHERE id = %s", (id,), commit=True)
    flash('Staff member removed', 'success')
    return redirect(url_for('staff'))

# Reports & Analytics
@app.route('/reports')
@login_required
def reports():
    # Total revenue
    total_revenue = execute_query(
        "SELECT COALESCE(SUM(total_amount), 0) as total FROM bills WHERE status = 'paid'",
        fetchone=True
    )
    
    # Total reservations
    total_reservations = execute_query(
        "SELECT COUNT(*) as count FROM reservations", fetchone=True
    )
    
    # Occupancy rate
    total_rooms = execute_query("SELECT COUNT(*) as count FROM rooms", fetchone=True)
    occupied_rooms = execute_query(
        "SELECT COUNT(*) as count FROM rooms WHERE status = 'Occupied'", fetchone=True
    )
    occupancy_rate = 0
    if total_rooms and total_rooms['count'] > 0:
        occupancy_rate = round((occupied_rooms['count'] / total_rooms['count']) * 100, 1)
    
    # Active staff
    active_staff = execute_query(
        "SELECT COUNT(*) as count FROM staff WHERE status = 'active'", fetchone=True
    )
    
    # Average rating
    avg_rating = execute_query(
        "SELECT COALESCE(AVG(rating), 0) as avg_rating FROM feedback", fetchone=True
    )
    
    # Reservations by status
    reservations_by_status = execute_query(
        """SELECT status, COUNT(*) as count FROM reservations 
           GROUP BY status ORDER BY count DESC"""
    )
    
    # Monthly revenue (last 6 months)
    monthly_revenue = execute_query(
        """SELECT DATE_FORMAT(payment_date, '%Y-%m') as month, 
                  SUM(total_amount) as revenue 
           FROM bills WHERE status = 'paid' 
           AND payment_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
           GROUP BY DATE_FORMAT(payment_date, '%Y-%m') 
           ORDER BY month"""
    )
    
    # Room type distribution
    room_types = execute_query(
        "SELECT room_type, COUNT(*) as count FROM rooms GROUP BY room_type"
    )
    
    # Recent feedback
    recent_feedback = execute_query(
        """SELECT f.*, r.guest_name, ro.room_number 
           FROM feedback f 
           JOIN reservations r ON f.reservation_id = r.id 
           JOIN rooms ro ON r.room_id = ro.id 
           ORDER BY f.feedback_date DESC LIMIT 5"""
    )
    
    return render_template('reports.html',
        total_revenue=float(total_revenue['total']) if total_revenue else 0,
        total_reservations=total_reservations['count'] if total_reservations else 0,
        occupancy_rate=occupancy_rate,
        active_staff=active_staff['count'] if active_staff else 0,
        avg_rating=round(float(avg_rating['avg_rating']), 1) if avg_rating else 0,
        reservations_by_status=reservations_by_status or [],
        monthly_revenue=convert_decimal(monthly_revenue) if monthly_revenue else [],
        room_types=room_types or [],
        recent_feedback=recent_feedback or []
    )

# Guest History & Search
@app.route('/guests')
@login_required
def guests():
    search = request.args.get('search', '')
    
    if search:
        guest_list = execute_query(
            """SELECT guest_name, guest_email, guest_phone, 
                      COUNT(*) as total_stays, 
                      SUM(payment_amount) as total_spent,
                      MAX(check_out) as last_visit
               FROM reservations 
               WHERE guest_name LIKE %s OR guest_email LIKE %s OR guest_phone LIKE %s
               GROUP BY guest_name, guest_email, guest_phone
               ORDER BY total_stays DESC""",
            (f'%{search}%', f'%{search}%', f'%{search}%')
        )
    else:
        guest_list = execute_query(
            """SELECT guest_name, guest_email, guest_phone, 
                      COUNT(*) as total_stays, 
                      SUM(payment_amount) as total_spent,
                      MAX(check_out) as last_visit
               FROM reservations 
               GROUP BY guest_name, guest_email, guest_phone
               ORDER BY total_stays DESC"""
        )
    
    guest_list = convert_decimal(guest_list) if guest_list else []
    
    return render_template('guests.html', guests=guest_list, search=search)

@app.route('/guests/<email>')
@login_required
def guest_history(email):
    try:
        history = execute_query(
            """SELECT r.*, ro.room_number, ro.room_type 
               FROM reservations r 
               JOIN rooms ro ON r.room_id = ro.id 
               WHERE r.guest_email = %s 
               ORDER BY r.check_in DESC""",
            (email,)
        )
        history = convert_decimal(history) if history else []
        
        # Convert dates to strings
        for item in history:
            item['check_in'] = str(item['check_in'])
            item['check_out'] = str(item['check_out'])
        
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Room Availability Calendar
@app.route('/rooms/calendar')
@login_required
def room_calendar():
    try:
        start_date = request.args.get('start', datetime.now().strftime('%Y-%m-%d'))
        end_date = request.args.get('end', (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'))
        
        rooms = execute_query("SELECT id, room_number, room_type, status FROM rooms ORDER BY room_number")
        
        reservations = execute_query(
            """SELECT room_id, check_in, check_out, status, guest_name 
               FROM reservations 
               WHERE check_out >= %s AND check_in <= %s
               AND status NOT IN ('cancelled')""",
            (start_date, end_date)
        )
        
        # Build calendar data
        calendar_data = []
        for room in rooms:
            room_entry = {
                'room_number': room['room_number'],
                'room_type': room['room_type'],
                'dates': {}
            }
            
            current = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            while current <= end:
                date_str = current.strftime('%Y-%m-%d')
                status = 'available'
                guest = ''
                
                if room['status'] == 'Maintenance':
                    status = 'maintenance'
                else:
                    for res in (reservations or []):
                        if res['room_id'] == room['id']:
                            ci = res['check_in'] if isinstance(res['check_in'], datetime) else datetime.strptime(str(res['check_in']), '%Y-%m-%d')
                            co = res['check_out'] if isinstance(res['check_out'], datetime) else datetime.strptime(str(res['check_out']), '%Y-%m-%d')
                            if ci <= current < co:
                                status = 'occupied'
                                guest = res['guest_name']
                                break
                
                room_entry['dates'][date_str] = {'status': status, 'guest': guest}
                current += timedelta(days=1)
            
            calendar_data.append(room_entry)
        
        return jsonify({
            'start': start_date,
            'end': end_date,
            'rooms': calendar_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Notifications
@app.route('/notifications')
@login_required
def notifications():
    all_notifications = execute_query(
        "SELECT * FROM notifications ORDER BY created_at DESC LIMIT 20"
    )
    return jsonify(all_notifications or [])

@app.route('/notifications/read/<int:id>', methods=['POST'])
@login_required
def mark_notification_read(id):
    execute_query("UPDATE notifications SET is_read = TRUE WHERE id = %s", (id,), commit=True)
    return jsonify({'message': 'Notification marked as read'}), 200

@app.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    execute_query("UPDATE notifications SET is_read = TRUE", commit=True)
    return jsonify({'message': 'All notifications marked as read'}), 200

# Context processor — inject unread notification count into every template
@app.context_processor
def inject_notifications():
    if 'user_id' in session:
        result = execute_query(
            "SELECT COUNT(*) as count FROM notifications WHERE is_read = FALSE",
            fetchone=True
        )
        return {'unread_notifications': result['count'] if result else 0}
    return {'unread_notifications': 0}

if __name__ == '__main__':
    app.run(debug=True)
