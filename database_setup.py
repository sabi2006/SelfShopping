import sqlite3


# --- INITIAL SETUP ---
# Connect to SQLite database (it will be created if it doesn't exist)
conn = sqlite3.connect('inventory.db')
cursor = conn.cursor()


# --- CREATE TABLES ---


# 1. Users Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
)
''')


# 2. Products Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    price REAL NOT NULL,
    barcodedata TEXT NOT NULL UNIQUE,
    location TEXT,
    image TEXT,
    description TEXT,
    category TEXT
)
''')


# 3. Purchase History Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS purchase_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price_per_unit REAL NOT NULL,
    purchase_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')


print("Tables created successfully.")


# --- POPULATE PRODUCTS TABLE WITH CORRECT BARCODES FROM PDF ---


# Sample product data with barcodes matching the PDF
products_to_add = [
    # Snacks
    (1, "Lays Potato Chips", 10.00, "2840019914", "Row 1-Sector 1", "/static/images/1.jpeg", "Classic salted potato chips.", "Snacks"),
    (2, "Slice 1.75 L", 93.00, "40189384", "Row 1-Sector 2", "/static/images/2.jpeg", "Sweet mango flavored drink.", "Beverages"),
    (3, "Tiger Biscuit", 10.00, "8901063164291", "Row 1-Sector 3", "/static/images/3.jpeg", "Crunchy glucose biscuits.", "Snacks"),
    (4, "Good Day Biscuit", 10.00, "8901063092716", "Row 1-Sector 4", "/static/images/4.jpeg", "Buttery cashew biscuits.", "Snacks"),
    (7, "Dark Fantasy Choco Fills", 128.00, "8901725017927", "Row 2-Sector 2", "/static/images/7.jpeg", "Chocolate-filled cookies.", "Snacks"),
    (8, "Sunfeast YiPPee Noodles", 153.00, "8901725132873", "Row 2-Sector 3", "/static/images/8.jpeg", "Instant noodles family pack.", "Instant Meals"),
    (21, "Oreo Chocolatey Biscuit", 87.00, "7622201703011", "Row 5-Sector 1", "/static/images/21.jpeg", "Chocolate sandwich biscuits.", "Snacks"),
    (23, "Kwality Choco Flakes 1kg", 229.00, "8906014903394", "Row 5-Sector 3", "/static/images/23.jpeg", "Tasty choco flakes for breakfast.", "Cereals"),
    (25, "Britannia 50-50 Maska Chaska", 28.00, "8901063017221", "Row 5-Sector 5", "/static/images/25.jpg", "Buttery and savory biscuits.", "Snacks"),
    
    # Daily Use Products
    (5, "Tata Salt 1kg", 25.00, "8904043901015", "Row 1-Sector 5", "/static/images/5.jpeg", "Iodized cooking salt.", "Groceries"),
    (6, "Gold Winner Sunflower Oil 1L", 190.00, "8906010261078", "Row 2-Sector 1", "/static/images/6.jpeg", "Refined sunflower oil.", "Groceries"),
    (9, "Colgate MaxFresh Toothpaste", 72.00, "6001067021995", "Row 2-Sector 4", "/static/images/9.jpeg", "Cooling crystals for fresh breath.", "Personal Care"),
    (10, "Dabur Honey - 1kg", 391.00, "8901207027437", "Row 2-Sector 5", "/static/images/10.jpeg", "100% pure and natural honey.", "Groceries"),
    (11, "Mysore Sandal Soap 450g", 232.00, "8901287400991", "Row 3-Sector 1", "/static/images/11.jpeg", "Luxurious sandalwood soap pack.", "Personal Care"),
    (12, "Harpic Toilet Cleaner 1L", 396.00, "6161100950900", "Row 3-Sector 2", "/static/images/12.jpg", "Effective toilet bowl cleaner.", "Cleaning"),
    (13, "Parachute Coconut Oil", 126.00, "8901088203630", "Row 3-Sector 3", "/static/images/13.jpg", "Pure coconut oil for hair and skin.", "Personal Care"),
    (14, "Santoor Soap (Pack of 4)", 163.00, "8901399111013", "Row 3-Sector 4", "/static/images/14.jpg", "Sandal and turmeric soap.", "Personal Care"),
    (15, "Surf Excel Easy Wash 5 Kg", 650.00, "8901030602054", "Row 3-Sector 5", "/static/images/15.jpg", "Powerful stain removal detergent.", "Cleaning"),
    (16, "Dettol Liquid Hand Wash 675ml", 92.00, "6295120050040", "Row 4-Sector 1", "/static/images/16.jpeg", "Antibacterial hand wash.", "Personal Care"),
    (17, "Vanish Stain Remover 800ml", 199.00, "8410104080204", "Row 4-Sector 2", "/static/images/17.jpeg", "Stain remover for clothes.", "Cleaning"),
    (18, "Cadbury Bournvita 2 kg", 697.00, "7622202026621", "Row 4-Sector 3", "/static/images/18.jpeg", "Chocolate health drink.", "Beverages"),
    (19, "Dabur Red Toothpaste 800g", 330.00, "8901207046070", "Row 4-Sector 4", "/static/images/19.jpeg", "Ayurvedic toothpaste for oral care.", "Personal Care"),
    (20, "Ariel Matic Liquid Detergent 3.2L", 479.00, "4987176206695", "Row 4-Sector 5", "/static/images/20.jpg", "Liquid detergent for washing machines.", "Cleaning"),
    (22, "BOOST Nutrition Drink 750g", 380.00, "8901030913211", "Row 5-Sector 2", "/static/images/22.jpeg", "Chocolate energy drink powder.", "Beverages"),
    (24, "Softouch Fabric Conditioner 2L", 345.00, "8901399336812", "Row 5-Sector 4", "/static/images/24.jpeg", "Fabric conditioner with French perfume.", "Cleaning")
]


# Insert data into the products table, ignoring if it already exists
cursor.executemany('''
INSERT OR IGNORE INTO products (id, name, price, barcodedata, location, image, description, category) 
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
''', products_to_add)


conn.commit()
print(f"{cursor.rowcount} new products added to the database.")


# Close the connection
conn.close()
print("Database setup complete with barcodes matching PDF!")
