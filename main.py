from flask import Flask, render_template, request, jsonify, send_file, make_response, redirect, url_for, session, flash
import cv2
from pyzbar.pyzbar import decode
import pygame
import time
import pyttsx3
import mysql.connector
import threading
import qrcode
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
import re
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'your_secret_key'
scanning = False
products = []  # List of dictionaries with product info 
total_prize = 0


# Sample product data with locations and corrected image paths
products12 = {
    "Snacks": [
        {"id": 1, "name": "Lays Potato Chips","price": 10.00 ,"location": "Row 1-Sector 1", "image": "/static/images/1.jpeg", "description": "Delicious potato chips."},
        {"id": 2, "name": "Slice 1.75 L","price": 93.00 ,"location": "Row 1-Sector 2", "image": "/static/images/2.jpeg", "description": "Refreshing beverage."},
        {"id": 3, "name": "Tiger Biscuit","price":10.00 , "location": "Row 1-Sector 3", "image": "/static/images/3.jpeg", "description": "Crunchy and tasty biscuits."},
        {"id": 4, "name": "Good Day Biscuit","price":10.00 , "location": "Row 1-Sector 4", "image": "/static/images/4.jpeg", "description": "Sweet and buttery biscuits."},
        {"id": 7, "name": "DARK FANTASY CHOCO FILLS LUXURIA","price":128.00 , "location": "Row 2-Sector 2", "image": "/static/images/7.jpeg", "description": "Delicious chocolate-filled cookies."},
        {"id": 8, "name": "Sunfeast YiPPee Family Pack", "price":153.00 ,"location": "Row 2-Sector 3", "image": "/static/images/8.jpeg", "description": "Tasty noodles for the whole family."},
        {"id": 21, "name": "Oreo Cadbury Chocolatey Biscuit","price":87.00 , "location": "Row 5-Sector 1", "image": "/static/images/21.jpeg", "description": "Delicious chocolate sandwich biscuits."},
        {"id": 23, "name": "Kwality Choco Flakes 1kg","price":229.00 , "location": "Row 5-Sector 3", "image": "/static/images/23.jpeg", "description": "Tasty choco flakes for breakfast."},
        {"id": 25, "name": "Britannia 50-50, Maska Chaska","price":28.00 , "location": "Row 5-Sector 5", "image": "/static/images/25.jpg", "description": "Crunchy biscuits with a tasty maska chaska."}
    ],
    "Daily Use Products": [
        {"id": 5, "name": "Tata Salt 1kg", "price":25.00 ,"location": "Row 1-Sector 5", "image": "/static/images/5.jpeg", "description": "Essential cooking salt."},
        {"id": 6, "name": "Gold Winner Sunflower Oil 1L","price":190.00 , "location": "Row 2-Sector 1", "image": "/static/images/6.jpeg", "description": "High-quality sunflower oil."},
        {"id": 9, "name": "Colgate MaxFresh Toothpaste","price":72.00 , "location": "Row 2-Sector 4", "image": "/static/images/9.jpeg", "description": "Fresh breath toothpaste."},
        {"id": 10, "name": "Dabur Honey - 1kg","price":391.00 ,"location": "Row 2-Sector 5", "image": "/static/images/10.jpeg", "description": "Pure and natural honey."},
        {"id": 11, "name": "Mysore Sandal Soap, 450g","price":232.00 , "location": "Row 3-Sector 1", "image": "/static/images/11.jpeg", "description": "Luxurious sandalwood soap."},
        {"id": 12, "name": "Harpic 1 Litre (Pack of 2)","price":396.00 , "location": "Row 3-Sector 2", "image": "/static/images/12.jpg", "description": "Effective toilet cleaner."},
        {"id": 13, "name": "Parachute Coconut Oil","price":126.00 , "location": "Row 3-Sector 3", "image": "/static/images/13.jpg", "description": "Pure coconut oil for cooking and skin."},
        {"id": 14, "name": "Santoor Soap (Pack of 4)","price":163.00 , "location": "Row 3-Sector 4", "image": "/static/images/14.jpg", "description": "Gentle and moisturizing soap."},
        {"id": 15, "name": "Surf Excel Easy Wash Detergent Powder - 5 Kg","price":650.00 , "location": "Row 3-Sector 5", "image": "/static/images/15.jpg", "description": "Powerful stain removal detergent."},
        {"id": 16, "name": "Dettol Liquid Hand Wash, 675ml","price":92.00 , "location": "Row 4-Sector 1", "image": "/static/images/16.jpeg", "description": "Antibacterial hand wash."},
        {"id": 17, "name": "Vanish 800ml","price":199.00 , "location": "Row 4-Sector 2", "image": "/static/images/17.jpeg", "description": "Stain remover for clothes."},
        {"id": 18, "name": "Cadbury Bournvita Chocolate Nutrition Drink, 2 kg","price":697.00 , "location": "Row 4-Sector 3", "image": "/static/images/18.jpeg", "description": "Chocolate drink for energy."},
        {"id": 19, "name": "Dabur Red Toothpaste - 800g (200gx4)","price":330.00 , "location": "Row 4-Sector 4", "image": "/static/images/19.jpeg", "description": "Ayurvedic toothpaste for oral care."},
        {"id": 20, "name": "Ariel Matic Liquid Detergent 3.2 Ltr","price":479.00 , "location": "Row 4-Sector 5", "image": "/static/images/20.jpg", "description": "Liquid detergent for washing machines."},
        {"id": 22, "name": "BOOST Chocolate Nutrition Drink Powder 750g","price":380.00 , "location": "Row 5-Sector 2", "image": "/static/images/22.jpeg", "description": "Chocolate drink powder for energy."},
        {"id": 24, "name": "Softouch 2X French Perfume 2L Fabric Conditioner","price":345.00 , "location": "Row 5-Sector 4", "image": "/static/images/24.jpeg", "description": "Fabric conditioner with a French fragrance."}
    ]
}


# Configure MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Harish@2006",
    database="barcodeDB"
)
cursor = db.cursor()


@app.route('/')
def home():
    if 'loggedin' in session:
        return redirect(url_for('home_page'))
    else:
        return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Validate the email
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address.')
        else:
            cursor.execute('SELECT * FROM users WHERE username = %s OR email = %s', (username, email))
            account = cursor.fetchone()

            if account:
                flash('Account with this username or email already exists.')
            else:
                cursor.execute('INSERT INTO users (username, password, email, created_at) VALUES (%s, %s, %s, %s)',
                               (username, hashed_password, email, datetime.now()))
                db.commit()
                flash('You have successfully registered!')
                return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account and check_password_hash(account[2], password):
            session['loggedin'] = True
            session['username'] = account[1]
            flash('Login successful!')
            return redirect(url_for('home_page'))
        else:
            flash('Invalid credentials, please try again.')

    return render_template('login.html')


@app.route('/home')
def home_page():
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('login'))


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    flash('You have successfully logged out.')
    return redirect(url_for('login'))


@app.route('/scanner')
def index():
    return render_template('index.html')


@app.route('/searchproduct')
def searchf():
    return render_template('gallery.html', products=products12)


@app.route('/product/<int:product_id>')
def product_details(product_id):
    product = next((p for category in products12.values() for p in category if p['id'] == product_id), None)
    if product is None:
        return render_template('404.html'), 404
    return render_template('shelves.html', product=product)


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    result = [product for category in products12.values() for product in category if query.lower() in product['name'].lower()]
    return jsonify(result)


@app.route('/register', methods=['POST'])
def register_user():
    data = request.json
    phone_number = data.get('phone_number')
    name = data.get('name')
    address = data.get('address')

    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Harish@2006",
        database="barcodeDB"
    )
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO users (phone_number, name, address) 
        VALUES (%s, %s, %s) 
        ON DUPLICATE KEY UPDATE name=VALUES(name), address=VALUES(address)
    """, (phone_number, name, address))
    db.commit()

    cursor.execute("SELECT id FROM users WHERE phone_number = %s", (phone_number,))
    user_id = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return jsonify({"status": "User registered", "user_id": user_id})


@app.route('/user-details', methods=['GET'])
def get_user_details():
    user_id = request.args.get('user_id')

    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Harish@2006",
        database="barcodeDB"
    )
    cursor = db.cursor()

    cursor.execute("SELECT phone_number, name, address FROM users WHERE id = %s", (user_id,))
    user_details = cursor.fetchone()
    cursor.close()
    db.close()

    if user_details:
        response = {
            "phone_number": user_details[0],
            "name": user_details[1],
            "address": user_details[2]
        }
    else:
        response = {"status": "User not found"}

    return jsonify(response)


def barcode_scanner(user_id, delay):
    global scanning, products, total_prize
    products = []
    total_prize = 0

    pygame.mixer.init()
    beep_sound = pygame.mixer.Sound("beep-02.mp3")
    success_sound = pygame.mixer.Sound("success.mp3")
    thank_you_sound = pygame.mixer.Sound("thankyou.mp3")
    wel = pygame.mixer.Sound("welcome.mp3")

    engine = pyttsx3.init()

    db1 = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Harish@2006",
        database="barcodeDB"
    )
    cursor = db1.cursor()

    camera_index = 0
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    wel.play()

    try:
        while scanning:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("Error: Failed to capture frame.")
                continue

            barcodes = decode(frame)

            for barcode in barcodes:
                (x, y, w, h) = barcode.rect
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                barcode_data = barcode.data.decode("utf-8")
                beep_sound.play()

                cursor.execute("SELECT product_name, product_price FROM products WHERE barcodedata = %s", (barcode_data,))
                result = cursor.fetchone()

                if result:
                    product_name, product_price = result
                    existing_product = next((product for product in products if product["name"] == product_name), None)

                    if existing_product:
                        existing_product["quantity"] += 1
                    else:
                        products.append({"name": product_name, "price": product_price, "quantity": 1})

                    total_prize += product_price
                    success_sound.play()

            cv2.imshow('Barcode Scanner', frame)
            time.sleep(delay)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):
                cap.release()
                camera_index = (camera_index + 1) % 2  # Assuming you have 2 cameras
                cap = cv2.VideoCapture(camera_index)

        engine.say(f"Total prize is {total_prize} rupees")
        engine.runAndWait()
        thank_you_sound.play()

        # Save purchase history
        try:
            for product in products:
                cursor.execute("""
                    INSERT INTO purchase_history (user_id, product_name, product_price, quantity, total)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, product['name'], product['price'], product['quantity'], product['price'] * product['quantity']))
            db1.commit()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            db1.rollback()

    finally:
        cap.release()
        cv2.destroyAllWindows()
        cursor.close()
        db1.close()


@app.route('/start', methods=['POST'])
def start_scanning():
    data = request.json
    user_id = data.get('user_id')
    delay = data.get('delay', 1)

    global scanning
    scanning = True
    threading.Thread(target=barcode_scanner, args=(user_id, delay)).start()
    return jsonify({"status": "Scanning started"})


@app.route('/stop', methods=['POST'])
def stop_scanning():
    global scanning
    scanning = False
    return jsonify({"status": "Scanning stopped", "products": products, "total_prize": total_prize})


@app.route('/remove', methods=['POST'])
def remove_item():
    global products, total_prize

    product_name = request.json.get('product_name')

    db1 = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Harish@2006",
        database="barcodeDB"
    )
    cursor = db1.cursor()

    cursor.execute("SELECT product_price FROM products WHERE product_name = %s", (product_name,))
    result = cursor.fetchone()
    if result:
        product_price = result[0]
        for product in products:
            if product['name'] == product_name:
                total_prize -= product['price'] * product['quantity']
                products.remove(product)
                break

    cursor.close()
    db1.close()

    return jsonify({"status": "Item removed", "products": products, "total_prize": total_prize})


@app.route('/change-quantity', methods=['POST'])
def change_quantity():
    global products, total_prize

    product_name = request.json.get('product_name')
    new_quantity = request.json.get('quantity')

    for product in products:
        if product['name'] == product_name:
            total_prize -= product['price'] * product['quantity']
            product['quantity'] = new_quantity
            total_prize += product['price'] * new_quantity
            break

    return jsonify({"status": "Quantity updated", "products": products, "total_prize": total_prize})


@app.route('/qr', methods=['GET'])
def generate_qr_code():
    payment_url = f"upi://pay?pa=bavaharishkumar-2@okicici&pn=VS STORES&am={total_prize}&cu=INR&mode=02"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(payment_url)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')

    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')


@app.route('/get-scanned-items', methods=['GET'])
def get_scanned_items():
    global products, total_prize
    return jsonify({"products": products, "total_prize": total_prize})


@app.route('/add-more', methods=['POST'])
def add_more():
    global scanning
    if not scanning:
        data = request.json
        user_id = data.get('user_id')
        delay = data.get('delay', 1)
        scanning = True
        threading.Thread(target=barcode_scanner, args=(user_id, delay)).start()
        return jsonify({"status": "Scanning resumed"})
    else:
        return jsonify({"status": "Scanning already in progress"})


@app.route('/generate-bill', methods=['GET'])
def generate_bill():
    global products, total_prize

    bill_html = render_template('bill.html', products=products, total_prize=total_prize)
    response = make_response(bill_html)
    response.headers['Content-Type'] = 'text/html'
    return response


@app.route('/predict', methods=['GET'])
def predict_products():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    username = session['username']
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT user_id FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        return jsonify([])

    user_id = user['user_id']

    cursor.execute("""
        SELECT product_name, COUNT(*) as freq
        FROM purchase_history
        WHERE user_id = %s
        GROUP BY product_name
        ORDER BY freq DESC
        LIMIT 3
    """, (user_id,))
    results = cursor.fetchall()

    # Save recommendations into database
    for r in results:
        cursor.execute("""
            INSERT INTO recommendations (user_id, product_name)
            VALUES (%s, %s)
        """, (user_id, r['product_name']))

    db.commit()
    cursor.close()

    return jsonify([r['product_name'] for r in results])


if __name__ == '__main__':
    app.run(debug=True)
