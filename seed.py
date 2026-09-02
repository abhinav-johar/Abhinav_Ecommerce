"""
Run this once to populate sample data:
    python seed.py
Re-run anytime after wiping tables to reset test data.
"""
from app import create_app
from app.extensions import db, bcrypt
from app.models import (
    Category, Product, ProductVariant, User, Cart, Address,
    CartItem, Order, OrderItem, Payment, ProductImage,
)

app = create_app()

with app.app_context():
    # Clear existing data (order matters due to FKs — children before parents)
    Payment.query.delete()
    OrderItem.query.delete()
    Order.query.delete()
    CartItem.query.delete()
    ProductVariant.query.delete()
    ProductImage.query.delete()
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
            is_admin=True,
        )
        db.session.add(test_user)
        db.session.commit()

        # Every user gets exactly one cart (per your schema)
        cart = Cart(user_id=test_user.id)
        db.session.add(cart)
        db.session.commit()
    elif not test_user.is_admin:
        # Existing test user from before is_admin was seeded true - promote them
        test_user.is_admin = True
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
            image_url='products/tshirt_classic.jpg',
            category_id=men.id,
            is_active=True,
        ),
        Product(
            name='Slim Fit Jeans',
            description='Stretchable slim fit denim jeans.',
            price=1999.0,
            discount_price=1499.0,
            stock_quantity=30,
            image_url='products/jeans_slim.jpg',
            category_id=men.id,
            is_active=True,
        ),
        Product(
            name='Sync Workwear Jacket',
            description='Classic workwear jacket built in technical fabric for travel and everyday wear.',
            price=4999.0,
            discount_price=None,
            stock_quantity=20,
            image_url='products/jacket_workwear.jpg',
            category_id=men.id,
            is_active=True,
        ),
        Product(
            name='Floral Summer Dress',
            description='Lightweight floral print dress for summer.',
            price=1599.0,
            discount_price=None,
            stock_quantity=25,
            image_url='products/dress_floral.jpg',
            category_id=women.id,
            is_active=True,
        ),
        Product(
            name='High-Rise Leggings',
            description='Stretch leggings built for training and everyday wear.',
            price=1299.0,
            discount_price=999.0,
            stock_quantity=35,
            image_url='products/leggings_highrise.jpg',
            category_id=women.id,
            is_active=True,
        ),
        Product(
            name='Cropped Zip Jacket',
            description='Lightweight cropped jacket with full zip closure.',
            price=2199.0,
            discount_price=None,
            stock_quantity=18,
            image_url='products/jacket_cropped.jpg',
            category_id=women.id,
            is_active=True,
        ),
        Product(
            name='Running Sneakers',
            description='Breathable running shoes with cushioned sole.',
            price=2999.0,
            discount_price=2399.0,
            stock_quantity=40,
            image_url='products/sneakers_running.jpg',
            category_id=footwear.id,
            is_active=True,
        ),
        Product(
            name='Seam Classic Sneakers',
            description='Minimal court-style sneakers with a clean silhouette.',
            price=4999.0,
            discount_price=None,
            stock_quantity=22,
            image_url='products/sneakers_seam_classic.jpg',
            category_id=footwear.id,
            is_active=True,
        ),
        Product(
            name='Trail Sandals',
            description='Rugged sandals built for outdoor wear.',
            price=1499.0,
            discount_price=None,
            stock_quantity=28,
            image_url='products/sandals_trail.jpg',
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
        Product(
            name='Prime Flo Cap',
            description='Lightweight cap with breathable mesh panels.',
            price=699.0,
            discount_price=None,
            stock_quantity=45,
            image_url='products/cap_prime_flo.jpg',
            category_id=accessories.id,
            is_active=True,
        ),
        Product(
            name='Everyday Backpack',
            description='Durable backpack with padded laptop compartment.',
            price=2499.0,
            discount_price=1999.0,
            stock_quantity=15,
            image_url='products/backpack_everyday.jpg',
            category_id=accessories.id,
            is_active=True,
        ),
    ]

    db.session.add_all(products)
    db.session.commit()

    # ---------------- Extra Gallery Images ----------------
    # Product.image_url (set above) is the MAIN/cover image, shown on cards,
    # cart, and the mega menu. Anything listed here is ADDITIONAL photos
    # shown only in the gallery on the product detail page.
    #
    # Edit this dict once you've uploaded more photos per product to
    # app/static/images/products/ — key = product name (must match exactly),
    # value = list of extra filenames (relative to images/, same as image_url).
    extra_images = {
        'Classic Cotton T-Shirt': [
            # 'products/tshirt_classic_2.webp',
            # 'products/tshirt_classic_3.webp',
        ],
        'Slim Fit Jeans': [
            # 'products/jeans_slim_2.webp',
        ],
        'Running Sneakers': [
            # 'products/sneakers_running_2.webp',
            # 'products/sneakers_running_3.webp',
        ],
        # Add more product names here as you get more photos for them.
    }

    for product in products:
        urls = extra_images.get(product.name, [])
        for i, url in enumerate(urls):
            db.session.add(ProductImage(product_id=product.id, image_url=url, sort_order=i))

    db.session.commit()

    # ---------------- Variants ----------------
    tshirt = products[0]
    jeans = products[1]
    sneakers = products[6]

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