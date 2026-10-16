import os
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Database Models ---
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(100), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

# Initialize database tables and seed sample products
with app.app_context():
    db.create_all()
    if not Product.query.first():
        sample_products = [
            Product(name="Wireless Mouse", description="Ergonomic wireless mouse with USB receiver.", price=29.99, image_url="https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500&auto=format&fit=crop&q=60"),
            Product(name="Mechanical Keyboard", description="RGB backlit mechanical gaming keyboard.", price=89.99, image_url="https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500&auto=format&fit=crop&q=60"),
            Product(name="USB-C Hub", description="Multiport USB-C adapter with HDMI and USB 3.0.", price=45.50, image_url="https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=500&auto=format&fit=crop&q=60"),
            Product(name="Noise-Cancelling Headphones", description="Over-ear wireless headphones with deep bass.", price=129.99, image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop&q=60")
        ]
        db.session.add_all(sample_products)
        db.session.commit()

# --- Routes ---
@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/cart')
def cart():
    cart_session = session.get('cart', {})
    cart_items = []
    total = 0
    for product_id_str, quantity in cart_session.items():
        product = Product.query.get(int(product_id_str))
        if product:
            subtotal = product.price * quantity
            total += subtotal
            cart_items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = {}
    cart = session['cart']
    str_id = str(product_id)
    cart[str_id] = cart.get(str_id, 0) + 1
    session.modified = True
    flash('Product added to cart!', 'success')
    return redirect(url_for('index'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    str_id = str(product_id)
    if str_id in cart:
        del cart[str_id]
        session.modified = True
        flash('Product removed from cart.', 'info')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart_session = session.get('cart', {})
    if not cart_session:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        
        total_price = 0
        order_items_data = []
        for product_id_str, quantity in cart_session.items():
            product = Product.query.get(int(product_id_str))
            if product:
                subtotal = product.price * quantity
                total_price += subtotal
                order_items_data.append((product, quantity))

        # Save Order
        new_order = Order(customer_name=name, customer_email=email, total_price=total_price)
        db.session.add(new_order)
        db.session.commit()

        # Save Order Items
        for product, qty in order_items_data:
            item = OrderItem(order_id=new_order.id, product_id=product.id, quantity=qty, price=product.price)
            db.session.add(item)
        db.session.commit()

        # Clear Cart
        session.pop('cart', None)
        flash(f'Thank you for your order, {name}! Order #{new_order.id} placed successfully.', 'success')
        return redirect(url_for('index'))

    return render_template('checkout.html')

if __name__ == '__main__':
    app.run(debug=True)