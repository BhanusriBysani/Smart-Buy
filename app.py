from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from PIL import Image
import random
import json
import pandas as pd
import bcrypt
import re
import os
import string

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Static file serving
@app.route('/ProductImages/<path:filename>')
def serve_product_images(filename):
    return send_from_directory('ProductImages', filename)

@app.route('/styles/<path:filename>')
def serve_css(filename):
    return send_from_directory('styles', filename)

@app.route('/scripts/<path:filename>')
def serve_js(filename):
    return send_from_directory('scripts', filename)

EXCEL_FILE = 'user_data/users.xlsx'

# Utility to read users
def read_users():
    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=['username', 'password'])
        os.makedirs(os.path.dirname(EXCEL_FILE), exist_ok=True)
        df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
    return pd.read_excel(EXCEL_FILE, engine='openpyxl')

# Password strength checker
def is_strong_password(password):
    errors = []
    if len(password) < 8:
        errors.append("at least 8 characters")
    if not re.search(r'[A-Z]', password):
        errors.append("an uppercase letter")
    if not re.search(r'[a-z]', password):
        errors.append("a lowercase letter")
    if not re.search(r'[0-9]', password):
        errors.append("a digit")
    if not re.search(r'[^A-Za-z0-9]', password):
        errors.append("a special character")
    return errors

# Routes
@app.route('/')
def index():
    return redirect(url_for('signup'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    message = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        df = read_users()

        if username in df['username'].values:
            message = "Username already exists."
        else:
            missing = is_strong_password(password)
            if missing:
                message = "Password must contain: " + ", ".join(missing) + "."
            else:
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                new_user = pd.DataFrame([[username, hashed.decode('utf-8')]], columns=['username', 'password'])
                df = pd.concat([df, new_user], ignore_index=True)
                df.to_excel(EXCEL_FILE, index=False)
                message = "Signup successful! You can now log in."

    return render_template('signup.html', message=message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        df = read_users()
        user_row = df[df['username'] == username]

        if not user_row.empty:
            stored_hash = user_row.iloc[0]['password']
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                session['username'] = username
                return redirect(url_for('home'))
            else:
                message = "Invalid password."
        else:
            message = "Username not found."

    return render_template('login.html', message=message)

@app.route('/home')
def home():
    if 'username' in session:
        with open('ProductData/products.json', 'r') as f:
            products = json.load(f)
        return render_template('home.html', username=session['username'], products=products)
    return redirect(url_for('login'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        product_name = request.form.get('product_name')
        with open('ProductData/products.json', 'r') as f:
            products = json.load(f)
        product = next((p for p in products if p['name'] == product_name), None)
        if product:
            return render_template('checkout.html', product=product)
        else:
            return "Product not found", 404

    return redirect(url_for('home'))

@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    if 'username' not in session:
        return redirect(url_for('login'))

    order_details = {
        'username': session['username'],
        'product': request.form.get('product_name', 'Multiple Items'),
        'name': request.form['name'],
        'address': request.form['address'],
        'phone': request.form['phone'],
        'email': request.form['email'],
        'total_price': request.form.get('total_price', '0')
    }

    print("Order received:", order_details)
    return render_template('order_confirmed.html', order=order_details)

@app.route('/search')
def search():
    if 'username' not in session:
        return redirect(url_for('login'))

    query = request.args.get('query', '').lower().strip()
    query = query.translate(str.maketrans('', '', string.punctuation))

    with open('ProductData/products.json', 'r') as f:
        products = json.load(f)

    keywords = ['saree', 'dress', 'shirt', 'kurti', 'jeans', 'lehenga', 'top', 'gown']
    search_terms = [word for word in query.split() if word in keywords]

    if not search_terms:
        filtered_products = []
    else:
        filtered_products = [p for p in products if any(k in p['name'].lower() for k in search_terms)]

    return render_template('home.html', username=session['username'], products=filtered_products)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'username' not in session:
        return redirect(url_for('login'))

    product_name = request.form.get('product_name')
    session.setdefault('cart', []).append(product_name)
    session.modified = True
    return redirect(url_for('home'))

@app.route('/cart')
def cart():
    if 'username' not in session:
        return redirect(url_for('login'))

    cart_items = session.get('cart', [])

    with open('ProductData/products.json', 'r') as f:
        all_products = json.load(f)

    cart_products = []
    total_price = 0

    for name in cart_items:
        product = next((p for p in all_products if p['name'] == name), None)
        if product:
            product['price'] = float(product['price'])
            cart_products.append(product)
            total_price += product['price']

    return render_template('cart.html', cart_products=cart_products, total_price=total_price)

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    if 'username' not in session:
        return redirect(url_for('login'))

    product_name = request.form.get('product_name')
    if 'cart' in session:
        session['cart'] = [item for item in session['cart'] if item != product_name]
        session.modified = True

    return redirect(url_for('cart'))

@app.route('/checkout_cart', methods=['POST'])
def checkout_cart():
    if 'username' not in session:
        return redirect(url_for('login'))

    cart = session.get('cart', [])

    with open('ProductData/products.json', 'r') as f:
        all_products = json.load(f)

    selected_products = []
    total_price = 0

    for item_name in cart:
        product = next((p for p in all_products if p['name'] == item_name), None)
        if product:
            selected_products.append(product)
            total_price += float(product['price'])

    return render_template('checkout_cart.html', products=selected_products, total_price=total_price)


@app.context_processor
def inject_cart_count():
    cart = session.get('cart', [])
    return dict(cart_count=len(cart))
@app.route('/confirm_cart_order', methods=['POST'])
def confirm_cart_order():
    name = request.form['name']
    address = request.form['address']
    phone = request.form['phone']
    email = request.form['email']
    cart_names = session.get('cart', [])

    with open('ProductData/products.json', 'r') as f:
        all_products = json.load(f)

    cart_products = []
    total_price = 0

    for name_in_cart in cart_names:
        product = next((p for p in all_products if p['name'] == name_in_cart), None)
        if product:
            product['price'] = float(product['price'])  # Ensure price is float
            cart_products.append(product)
            total_price += product['price']

    # Clear cart after order
    session.pop('cart', None)

    # You can save or log the order here if needed
    return render_template('order_confirmed.html', order={
        'name': name,
        'address': address,
        'phone': phone,
        'email': email,
        'total_price': total_price,
        'products': cart_products
    })
@app.route('/image_search', methods=['POST'])
def image_search():
    if 'image' not in request.files:
        return "No image uploaded", 400

    image = request.files['image']

    # Save image temporarily
    image_path = os.path.join('temp_uploads', image.filename)
    os.makedirs('temp_uploads', exist_ok=True)
    image.save(image_path)

    # 🔍 Step to extract keywords or match products
    # For now, we simulate it with filename or dummy match
    # Replace this with AI-based classification if needed
    keyword = os.path.splitext(image.filename)[0].lower()  # crude match using filename

    # Load product data
    with open('ProductData/products.json', 'r') as f:
        products = json.load(f)

    # Match products by filename keyword
    matched_products = [
        product for product in products if keyword in product['name'].lower()
    ]

    return render_template('home.html', products=matched_products, username=session.get('username', ''))



# Run the app
if __name__ == '__main__':
    app.run(debug=True)
