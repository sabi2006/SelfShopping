import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response
from werkzeug.security import generate_password_hash, check_password_hash
import cv2
from pyzbar.pyzbar import decode, ZBarSymbol
import threading
import time
import datetime
import numpy as np
import warnings
import qrcode
from io import BytesIO
import base64

# Suppress zbar warnings
warnings.filterwarnings('ignore')

# --- APP SETUP ---
app = Flask(__name__)
app.secret_key = 'your_super_secret_key'

# --- GLOBAL VARIABLES & LOCKS for scanning process ---
scanning = False
camera_lock = threading.Lock()
products_lock = threading.Lock()
scanned_products = []
total_price = 0
camera = None
last_detected_barcode = {'data': None, 'time': 0}

# --- DATABASE FUNCTIONS ---
def get_db_connection():
    conn = sqlite3.connect('inventory.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# --- AUTHENTICATION & CORE ROUTES ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if not username or not email or not password:
            flash('All fields are required!', 'danger')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', 
                        (username, email, hashed_password))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['loggedin'] = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
def index():
    return redirect(url_for('login')) if 'loggedin' not in session else redirect(url_for('home'))

@app.route('/home')
def home():
    if 'loggedin' in session:
        return render_template('home.html', username=session.get('username'))
    return redirect(url_for('login'))

@app.route('/scanner')
def scanner():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    global scanned_products, total_price, last_detected_barcode
    with products_lock:
        scanned_products = []
        total_price = 0
        last_detected_barcode = {'data': None, 'time': 0}
    session.pop('last_scanned', None)
    session.pop('scan_status', None)
    return render_template('scanner.html')

@app.route('/search')
def search_page():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    all_products = conn.execute("SELECT * FROM products ORDER BY category").fetchall()
    conn.close()
    products_by_category = {}
    for product in all_products:
        category = product['category']
        if category not in products_by_category:
            products_by_category[category] = []
        products_by_category[category].append(dict(product))
    return render_template('search.html', products_by_category=products_by_category)

@app.route('/product/<int:product_id>')
def product_details(product_id):
    conn = get_db_connection()
    product = conn.execute("SELECT id, name, location FROM products WHERE id = ?", 
                          (product_id,)).fetchone()
    conn.close()
    if product:
        return render_template('product_details.html', product=product)
    else:
        return "Product not found", 404

# --- CART MANAGEMENT ROUTES (NEW) ---
@app.route('/updatecart', methods=['POST'])
def update_cart():
    """Update quantity of a product in cart"""
    global scanned_products, total_price
    data = request.get_json()
    product_name = data.get("product_name")
    new_quantity = int(data.get("quantity"))
    
    if new_quantity < 1:
        return jsonify({"success": False, "message": "Quantity must be at least 1"})
    
    with products_lock:
        for item in scanned_products:
            if item['name'] == product_name:
                item['quantity'] = new_quantity
                break
        # Recalculate total
        total_price = sum(p['price'] * p['quantity'] for p in scanned_products)
    
    return jsonify({"success": True})

@app.route('/removecartitem', methods=['POST'])
def remove_cart_item():
    """Remove a product from cart"""
    global scanned_products, total_price
    data = request.get_json()
    product_name = data.get("product_name")
    
    with products_lock:
        scanned_products = [item for item in scanned_products if item['name'] != product_name]
        # Recalculate total
        total_price = sum(p['price'] * p['quantity'] for p in scanned_products)
    
    return jsonify({"success": True})

# --- BARCODE DETECTION LOGIC ---
def add_product_to_cart(barcode_data):
    """Looks up a product and adds it to the cart ONCE. Returns a status dictionary."""
    global scanned_products, total_price, last_detected_barcode
    
    # CRITICAL: Strict debouncing - detect each barcode only once with 3 second cooldown
    current_time = time.time()
    if (last_detected_barcode['data'] == barcode_data and 
        (current_time - last_detected_barcode['time']) < 3.0):
        return None  # Already processed, skip silently
    
    # Update last detected
    last_detected_barcode = {'data': barcode_data, 'time': current_time}
    
    try:
        conn = get_db_connection()
        product_info = conn.execute("SELECT * FROM products WHERE barcodedata = ?", 
                                   (barcode_data,)).fetchone()
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return {'status': 'error', 'message': 'Database error'}
    
    if not product_info:
        print(f"Barcode {barcode_data} not found in database")
        return {'status': 'error', 'message': f'Product not found'}
    
    product_name = product_info['name']
    product_price = product_info['price']
    
    try:
        with products_lock:
            found = False
            for p in scanned_products:
                if p['name'] == product_name:
                    p['quantity'] += 1
                    found = True
                    break
            
            if not found:
                scanned_products.append({
                    'name': product_name,
                    'price': product_price,
                    'quantity': 1
                })
            
            total_price += product_price
        
        print(f"✓ Successfully added: {product_name} - ₹{product_price}")
        return {'status': 'success', 'message': f'Added: {product_name}'}
    
    except Exception as e:
        print(f"Error updating cart: {e}")
        return {'status': 'error', 'message': 'Error updating cart'}

def process_frame_for_barcodes(frame):
    """Detects barcodes with optimized single-detection per barcode."""
    global last_detected_barcode
    
    height, width = frame.shape[:2]
    
    # Draw scanning guide
    guide_margin_x = int(width * 0.15)
    guide_margin_y = int(height * 0.25)
    cv2.rectangle(frame, 
                 (guide_margin_x, guide_margin_y),
                 (width - guide_margin_x, height - guide_margin_y),
                 (0, 255, 0), 2)
    
    # Center scanning line
    center_y = height // 2
    cv2.line(frame, (guide_margin_x, center_y),
            (width - guide_margin_x, center_y), (0, 255, 0), 2)
    
    # OPTIMIZED: Only scan for common barcode types
    try:
        barcodes = decode(frame, symbols=[
            ZBarSymbol.EAN13, ZBarSymbol.EAN8, ZBarSymbol.UPCA,
            ZBarSymbol.UPCE, ZBarSymbol.CODE39, ZBarSymbol.CODE128,
            ZBarSymbol.QRCODE
        ])
    except:
        barcodes = []
    
    # If nothing found on full frame, try grayscale
    if not barcodes:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        try:
            barcodes = decode(gray, symbols=[
                ZBarSymbol.EAN13, ZBarSymbol.EAN8, ZBarSymbol.UPCA,
                ZBarSymbol.UPCE, ZBarSymbol.CODE39, ZBarSymbol.CODE128
            ])
        except:
            barcodes = []
    
    # Process ONLY the first detected barcode
    if barcodes:
        barcode = barcodes[0]
        try:
            barcode_data = barcode.data.decode('utf-8')
            barcode_type = barcode.type
            (x, y, w, h) = barcode.rect
            
            current_time = time.time()
            is_recent = (last_detected_barcode['data'] == barcode_data and 
                        (current_time - last_detected_barcode['time']) < 3.0)
            
            if is_recent:
                color = (255, 165, 0)  # Orange for cooldown
                status_text = "Already scanned - wait 3s"
            else:
                scan_result = add_product_to_cart(barcode_data)
                if scan_result:
                    if scan_result['status'] == 'success':
                        color = (0, 255, 0)  # Green
                        status_text = scan_result['message']
                        session['scan_status'] = scan_result
                    else:
                        color = (0, 0, 255)  # Red
                        status_text = scan_result['message']
                        session['scan_status'] = scan_result
                else:
                    color = (255, 165, 0)
                    status_text = "Processing..."
            
            # Draw detection rectangle
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)
            
            # Draw corner markers
            corner_len = 25
            thickness = 4
            # Top-left
            cv2.line(frame, (x, y), (x + corner_len, y), color, thickness)
            cv2.line(frame, (x, y), (x, y + corner_len), color, thickness)
            # Top-right
            cv2.line(frame, (x + w, y), (x + w - corner_len, y), color, thickness)
            cv2.line(frame, (x + w, y), (x + w, y + corner_len), color, thickness)
            # Bottom-left
            cv2.line(frame, (x, y + h), (x + corner_len, y + h), color, thickness)
            cv2.line(frame, (x, y + h), (x, y + h - corner_len), color, thickness)
            # Bottom-right
            cv2.line(frame, (x + w, y + h), (x + w - corner_len, y + h), color, thickness)
            cv2.line(frame, (x + w, y + h), (x + w, y + h - corner_len), color, thickness)
            
            # Display barcode info
            text_y = y - 15 if y > 60 else y + h + 30
            text_size = cv2.getTextSize(f"{barcode_type}", cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(frame, (x, text_y - 25), (x + text_size[0] + 10, text_y + 5), (0, 0, 0), -1)
            cv2.putText(frame, f"{barcode_type}", (x + 5, text_y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            cv2.putText(frame, status_text, (x, text_y + 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        except Exception as e:
            print(f"Error processing barcode: {e}")
    
    # Status indicators
    cv2.putText(frame, 'SCANNING', (10, 35),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(frame, 'Hold barcode in green box',
               (guide_margin_x, height - 15),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    return frame

def generate_frames():
    """Generator function that yields camera frames for video streaming."""
    global camera, scanning
    
    with camera_lock:
        if camera is None:
            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                print("Error: Cannot open camera")
                return
            
            # Optimal camera settings
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            camera.set(cv2.CAP_PROP_FPS, 30)
            camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            
            # Flush buffer
            for _ in range(5):
                camera.read()
    
    frame_count = 0
    prev_time = time.time()
    
    while True:
        try:
            with camera_lock:
                if not scanning or camera is None:
                    if camera:
                        camera.release()
                        camera = None
                    break
                
                success, frame = camera.read()
            
            if not success:
                time.sleep(0.05)
                continue
            
            # Process frame for barcodes
            frame = process_frame_for_barcodes(frame)
            
            # Calculate FPS
            frame_count += 1
            current_time = time.time()
            if current_time - prev_time >= 1.0:
                fps = frame_count / (current_time - prev_time)
                frame_count = 0
                prev_time = current_time
            else:
                fps = 30
            
            cv2.putText(frame, f'FPS: {int(fps)}', (frame.shape[1] - 120, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Encode frame
            encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
            ret, buffer = cv2.imencode('.jpg', frame, encode_params)
            if not ret:
                continue
            
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.03)
        
        except Exception as e:
            print(f"Error in frame generation: {e}")
            time.sleep(0.1)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_scan', methods=['POST'])
def start_scanning():
    global scanning, scanned_products, total_price, last_detected_barcode
    if not scanning:
        scanning = True
        with products_lock:
            scanned_products = []
            total_price = 0
            last_detected_barcode = {'data': None, 'time': 0}
        session.pop('last_scanned', None)
        session.pop('scan_status', None)
        print("🔵 Scanning started")
        return jsonify({"status": "Scanning started"})
    return jsonify({"status": "Already scanning"})

@app.route('/stop_scan', methods=['POST'])
def stop_scanning():
    global scanning
    scanning = False
    print("🔴 Scanning stopped")
    return jsonify({"status": "Scanning stopped"})

@app.route('/get_cart_data', methods=['GET'])
def get_cart_data():
    """Returns cart data and scan status."""
    with products_lock:
        response_data = {
            "products": scanned_products,
            "total_price": total_price
        }
    
    if 'scan_status' in session:
        response_data['scan_status'] = session.pop('scan_status')
    
    return jsonify(response_data)

@app.route('/generate_bill')
def generate_bill():
    """Generate bill with UPI QR code"""
    global scanned_products, total_price
    
    # UPI details for demo
    upi_id = "sabimoney11@okaxis"
    upi_name = "Smart shopping"
    
    # Create UPI payment URL
    upi_url = f"upi://pay?pa={upi_id}&pn={upi_name}&am={total_price:.2f}&cu=INR"
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(upi_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    now = datetime.datetime.now()
    
    return render_template('bill.html', 
                         products=scanned_products,
                         total_price=total_price, 
                         now=now,
                         qr_code=qr_code_base64,
                         upi_id=upi_id)

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
