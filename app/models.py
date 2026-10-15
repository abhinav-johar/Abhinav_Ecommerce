from datetime import datetime
from flask_login import UserMixin
from app.extensions import db, login_manager


# ==========================================================
# USER
# ==========================================================
class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    orders = db.relationship('Order', backref='user', lazy=True)
    addresses = db.relationship('Address', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)
    cart = db.relationship('Cart', backref='user', uselist=False, lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==========================================================
# CATEGORY
# ==========================================================
class Category(db.Model):
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)

    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'


# ==========================================================
# PRODUCT
# ==========================================================
class Product(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    fabric_care = db.Column(db.Text, nullable=True)
    technical_specification = db.Column(db.Text, nullable=True)
    warranty_info = db.Column(db.Text, nullable=True)
    shipping_returns = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    discount_price = db.Column(db.Float, nullable=True)
    stock_quantity = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(250))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    variants = db.relationship('ProductVariant', backref='product', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='product', lazy=True, cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    images = db.relationship('ProductImage', backref='product', lazy=True,
                              order_by='ProductImage.sort_order', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Product {self.name}>'


# ==========================================================
# PRODUCT IMAGE (extra gallery photos, beyond Product.image_url)
# ==========================================================
class ProductImage(db.Model):
    __tablename__ = 'product_image'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    image_url = db.Column(db.String(250), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    color = db.Column(db.String(30), nullable=True)  # optional tag, e.g. 'Black' - lets clicking a color swatch show only that color's photos

    def __repr__(self):
        return f'<ProductImage product_id={self.product_id} url={self.image_url} color={self.color}>'


# ==========================================================
# PRODUCT VARIANT
# ==========================================================
class ProductVariant(db.Model):
    __tablename__ = 'product_variant'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    size = db.Column(db.String(10))
    color = db.Column(db.String(30))
    stock_quantity = db.Column(db.Integer, default=0)
    sku = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<ProductVariant {self.sku}>'


# ==========================================================
# ADDRESS
# ==========================================================
class Address(db.Model):
    __tablename__ = 'address'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    address_line1 = db.Column(db.String(200), nullable=False)
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    is_default = db.Column(db.Boolean, default=False)

    # Relationships
    orders = db.relationship('Order', backref='address', lazy=True)

    def __repr__(self):
        return f'<Address {self.city}, {self.state}>'


# ==========================================================
# CART
# ==========================================================
class Cart(db.Model):
    __tablename__ = 'cart'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    items = db.relationship('CartItem', backref='cart', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Cart user_id={self.user_id}>'


# ==========================================================
# CART ITEM
# ==========================================================
class CartItem(db.Model):
    __tablename__ = 'cart_item'

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_at_time = db.Column(db.Float, nullable=False)

    # Relationships
    variant = db.relationship('ProductVariant', lazy=True)

    def __repr__(self):
        return f'<CartItem product_id={self.product_id} qty={self.quantity}>'


# ==========================================================
# ORDER
# ==========================================================
class Order(db.Model):
    __tablename__ = 'order'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending/shipped/delivered/cancelled
    payment_status = db.Column(db.String(20), default='unpaid')  # paid/unpaid/refunded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    payment = db.relationship('Payment', backref='order', uselist=False, lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Order #{self.id} status={self.status}>'


# ==========================================================
# ORDER ITEM
# ==========================================================
class OrderItem(db.Model):
    __tablename__ = 'order_item'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)

    # Relationships
    variant = db.relationship('ProductVariant', lazy=True)

    def __repr__(self):
        return f'<OrderItem order_id={self.order_id} product_id={self.product_id}>'


# ==========================================================
# PAYMENT
# ==========================================================
class Payment(db.Model):
    __tablename__ = 'payment'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False, unique=True)
    payment_method = db.Column(db.String(30))  # UPI / Card / COD
    transaction_id = db.Column(db.String(100))
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    paid_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Payment order_id={self.order_id} status={self.status}>'


# ==========================================================
# REVIEW
# ==========================================================
class Review(db.Model):
    __tablename__ = 'review'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Review product_id={self.product_id} rating={self.rating}>'