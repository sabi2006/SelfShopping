from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Sample product data with categories, locations, and corrected image paths
products12 = {
    "Snacks": [
        {"id": 1, "name": "Lays Potato Chips", "location": "Row 1-Sector 1", "image": "/static/images/1.jpeg", "description": "Delicious potato chips."},
        {"id": 2, "name": "Slice 1.75 L", "location": "Row 1-Sector 2", "image": "/static/images/2.jpeg", "description": "Refreshing beverage."},
        {"id": 3, "name": "Tiger Biscuit", "location": "Row 1-Sector 3", "image": "/static/images/3.jpeg", "description": "Crunchy and tasty biscuits."},
        {"id": 4, "name": "Good Day Biscuit", "location": "Row 1-Sector 4", "image": "/static/images/4.jpeg", "description": "Sweet and buttery biscuits."},
        {"id": 7, "name": "DARK FANTASY CHOCO FILLS LUXURIA", "location": "Row 2-Sector 2", "image": "/static/images/7.jpeg", "description": "Delicious chocolate-filled cookies."},
        {"id": 8, "name": "Sunfeast YiPPee Family Pack", "location": "Row 2-Sector 3", "image": "/static/images/8.jpeg", "description": "Tasty noodles for the whole family."},
        {"id": 21, "name": "Oreo Cadbury Chocolatey Flavour Crème Sandwich Biscuit, 288.75 Gram", "location": "Row 5-Sector 1", "image": "/static/images/21.jpeg", "description": "Delicious chocolate sandwich biscuits."},
        {"id": 23, "name": "Kwality Choco Flakes 1kg", "location": "Row 5-Sector 3", "image": "/static/images/23.jpeg", "description": "Tasty choco flakes for breakfast."},
        {"id": 25, "name": "Britannia 50-50, Maska Chaska, 105 gram", "location": "Row 5-Sector 5", "image": "/static/images/25.jpg", "description": "Crunchy biscuits with a tasty maska chaska."}
    ],
    "Daily Use Products": [
        
        {"id": 5, "name": "Tata Salt 1kg", "location": "Row 1-Sector 5", "image": "/static/images/5.jpeg", "description": "Essential cooking salt."},
        {"id": 6, "name": "Gold Winner Sunflower Oil 1L", "location": "Row 2-Sector 1", "image": "/static/images/6.jpeg", "description": "High-quality sunflower oil."},
        {"id": 9, "name": "Colgate MaxFresh Toothpaste", "location": "Row 2-Sector 4", "image": "/static/images/9.jpeg", "description": "Fresh breath toothpaste."},
        {"id": 10, "name": "Dabur Honey - 1kg", "location": "Row 2-Sector 5", "image": "/static/images/10.jpeg", "description": "Pure and natural honey."},
        {"id": 11, "name": "Mysore Sandal Soap, 450g", "location": "Row 3-Sector 1", "image": "/static/images/11.jpeg", "description": "Luxurious sandalwood soap."},
        {"id": 12, "name": "Harpic 1 Litre (Pack of 2)", "location": "Row 3-Sector 2", "image": "/static/images/12.jpg", "description": "Effective toilet cleaner."},
        {"id": 13, "name": "Parachute Coconut Oil", "location": "Row 3-Sector 3", "image": "/static/images/13.jpg", "description": "Pure coconut oil for cooking and skin."},
        {"id": 14, "name": "Santoor Soap (Pack of 4)", "location": "Row 3-Sector 4", "image": "/static/images/14.jpg", "description": "Gentle and moisturizing soap."},
        {"id": 15, "name": "Surf Excel Easy Wash Detergent Powder - 5 Kg", "location": "Row 3-Sector 5", "image": "/static/images/15.jpg", "description": "Powerful stain removal detergent."},
        {"id": 16, "name": "Dettol Liquid Hand Wash, 675ml", "location": "Row 4-Sector 1", "image": "/static/images/16.jpeg", "description": "Antibacterial hand wash."},
        {"id": 17, "name": "Vanish 800ml", "location": "Row 4-Sector 2", "image": "/static/images/17.jpeg", "description": "Stain remover for clothes."},
        {"id": 18, "name": "Cadbury Bournvita Chocolate Nutrition Drink, 2 kg", "location": "Row 4-Sector 3", "image": "/static/images/18.jpeg", "description": "Chocolate drink for energy."},
        {"id": 19, "name": "Dabur Red Toothpaste - 800g (200gx4)", "location": "Row 4-Sector 4", "image": "/static/images/19.jpeg", "description": "Ayurvedic toothpaste for oral care."},
        {"id": 20, "name": "Ariel Matic Liquid Detergent 3.2 Ltr", "location": "Row 4-Sector 5", "image": "/static/images/20.jpg", "description": "Liquid detergent for washing machines."},
        {"id": 22, "name": "BOOST Chocolate Nutrition Drink Powder 750g", "location": "Row 5-Sector 2", "image": "/static/images/22.jpeg", "description": "Chocolate drink powder for energy."},
        {"id": 24, "name": "Softouch 2X French Perfume 2L Fabric Conditioner", "location": "Row 5-Sector 4", "image": "/static/images/24.jpeg", "description": "Fabric conditioner with a French fragrance."},

        
    ]
}

@app.route('/')
def index():
    # Render the product gallery with all products
    return render_template('gallery.html', products=products12)

@app.route('/product/<int:product_id>')
def product_details(product_id):
    # Find the product by its ID
    product = next((p for category in products12.values() for p in category if p['id'] == product_id), None)
    if product is None:
        return render_template('404.html'), 404
    # Render the product shelf page
    return render_template('shelves.html', product=product)

@app.route('/search', methods=['GET'])
def search():
    # Get the search query from the request
    query = request.args.get('query', '')
    # Filter products based on the query (case-insensitive)
    result = [product for category in products12.values() for product in category if query.lower() in product['name'].lower()]
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
