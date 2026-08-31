"""
Run this once to populate sample data:
    python seed.py
Re-run anytime after wiping tables to reset test data.
"""
from app import create_app
from app.extensions import db, bcrypt
from app.models import (
    Category, Product, ProductVariant, User, Cart, Address,
    CartItem, Order, OrderItem, Payment,
)

app = create_app()

with app.app_context():
    # Clear existing data (order matters due to FKs — children before parents)
    Payment.query.delete()
    OrderItem.query.delete()
    Order.query.delete()
    CartItem.query.delete()
    ProductVariant.query.delete()
    Product.query.delete()
    Category.query.delete()
    db.session.commit()

    # ---------------- Test User (temporary, until auth is built) ----------------
    test_user = User.query.filter_by(email='test@one8.com').first()
    if not test_user:
        test_user = User(
            name='Test User',
            email='test@one8.com',
            password_hash=bcrypt.generate_password_hash('password123').decode('utf-8'),
            phone='9999999999',
            is_admin=False,
        )
        db.session.add(test_user)
        db.session.commit()

        # Every user gets exactly one cart (per your schema)
        cart = Cart(user_id=test_user.id)
        db.session.add(cart)
        db.session.commit()

    # ---------------- Test Address (temporary, until 'add address' form is built) ----------------
    test_address = Address.query.filter_by(user_id=test_user.id).first()
    if not test_address:
        test_address = Address(
            user_id=test_user.id,
            full_name='Test User',
            phone='9999999999',
            address_line1='123 MG Road',
            address_line2='Near City Mall',
            city='Bengaluru',
            state='Karnataka',
            pincode='560001',
            is_default=True,
        )
        db.session.add(test_address)
        db.session.commit()

    print(f'Test user id: {test_user.id} (email: {test_user.email})')

    # ---------------- Categories ----------------
    men = Category(name='Men', slug='men')
    women = Category(name='Women', slug='women')
    footwear = Category(name='Footwear', slug='footwear')
    accessories = Category(name='Accessories', slug='accessories')

    db.session.add_all([men, women, footwear, accessories])
    db.session.commit()

    # ---------------- Products ----------------
    products = [
        Product(
            name='Classic Cotton T-Shirt',
            description='A comfortable everyday cotton t-shirt.',
            price=799.0,
            discount_price=599.0,
            stock_quantity=50,
            image_url='products/tshirt_classic.webp',
            category_id=men.id,
            is_active=True,
        ),
        Product(
            name='Slim Fit Jeans',
            description='Stretchable slim fit denim jeans.',
            price=1999.0,
            discount_price=1499.0,
            stock_quantity=30,
            image_url='products/jeans_slim.webp',
            category_id=men.id,
            is_active=True,
        ),
        Product(
            name='Floral Summer Dress',
            description='Lightweight floral print dress for summer.',
            price=1599.0,
            discount_price=None,
            stock_quantity=25,
            image_url='products/dress_floral_summer.jpg',
            category_id=women.id,
            is_active=True,
        ),
        Product(
            name='Running Sneakers',
            description='Breathable running shoes with cushioned sole.',
            price=2999.0,
            discount_price=2399.0,
            stock_quantity=40,
            image_url='products/sneaker_running.webp',
            category_id=footwear.id,
            is_active=True,
        ),
        Product(
            name='Leather Wallet',
            description='Genuine leather bifold wallet.',
            price=899.0,
            discount_price=None,
            stock_quantity=60,
            image_url='products/wallet_leather.jpg',
            category_id=accessories.id,
            is_active=True,
        ),
    ]

    db.session.add_all(products)
    db.session.commit()

    # ---------------- Variants ----------------
    tshirt = products[0]
    jeans = products[1]
    sneakers = products[3]

    variants = [
        ProductVariant(product_id=tshirt.id, size='S', color='Black', stock_quantity=15, sku='TSHIRT-BLK-S'),
        ProductVariant(product_id=tshirt.id, size='M', color='Black', stock_quantity=20, sku='TSHIRT-BLK-M'),
        ProductVariant(product_id=tshirt.id, size='L', color='White', stock_quantity=15, sku='TSHIRT-WHT-L'),

        ProductVariant(product_id=jeans.id, size='30', color='Blue', stock_quantity=10, sku='JEANS-BLU-30'),
        ProductVariant(product_id=jeans.id, size='32', color='Blue', stock_quantity=10, sku='JEANS-BLU-32'),
        ProductVariant(product_id=jeans.id, size='34', color='Black', stock_quantity=10, sku='JEANS-BLK-34'),

        ProductVariant(product_id=sneakers.id, size='8', color='White', stock_quantity=15, sku='SNKR-WHT-8'),
        ProductVariant(product_id=sneakers.id, size='9', color='Grey', stock_quantity=15, sku='SNKR-GRY-9'),
        ProductVariant(product_id=sneakers.id, size='10', color='Black', stock_quantity=10, sku='SNKR-BLK-10'),
    ]

    db.session.add_all(variants)
    db.session.commit()

    print(f'Seeded {Category.query.count()} categories, '
          f'{Product.query.count()} products, '
          f'{ProductVariant.query.count()} variants.')