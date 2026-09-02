"""
Run once to remove the ORIGINAL demo products created by seed.py,
leaving any products you've since added through the admin panel intact.

Usage:
    python cleanup_seed_products.py

Safe to re-run - products already removed (or never seeded) are skipped.
"""
from app import create_app
from app.extensions import db
from app.models import Product, ProductVariant, ProductImage, CartItem

app = create_app()

# Exact names of the products originally created by seed.py.
# Anything added later via the admin panel won't match this list
# and will be left alone.
SEEDED_PRODUCT_NAMES = [
    'Classic Cotton T-Shirt',
    'Slim Fit Jeans',
    'Sync Workwear Jacket',
    'Floral Summer Dress',
    'High-Rise Leggings',
    'Cropped Zip Jacket',
    'Running Sneakers',
    'Seam Classic Sneakers',
    'Trail Sandals',
    'Leather Wallet',
    'Prime Flo Cap',
    'Everyday Backpack',
]

with app.app_context():
    deleted_count = 0
    deactivated_count = 0
    not_found_count = 0

    for name in SEEDED_PRODUCT_NAMES:
        product = Product.query.filter_by(name=name).first()

        if not product:
            not_found_count += 1
            continue

        # Remove any stale cart items pointing at this product first -
        # these are just leftover test-cart entries, safe to clear.
        CartItem.query.filter_by(product_id=product.id).delete()
        db.session.commit()

        # ProductVariant and ProductImage cascade-delete automatically
        # (cascade='all, delete-orphan' on the Product relationships).
        try:
            db.session.delete(product)
            db.session.commit()
            print(f'Deleted: {name}')
            deleted_count += 1
        except Exception:
            # Product is referenced by a real OrderItem (past order history) -
            # can't hard-delete without breaking that order, so deactivate instead.
            db.session.rollback()
            product.is_active = False
            db.session.commit()
            print(f'Could not delete "{name}" (linked to a past order) - deactivated instead.')
            deactivated_count += 1

    print()
    print(f'Done. Deleted: {deleted_count}, Deactivated: {deactivated_count}, '
          f'Not found (already removed or never existed): {not_found_count}')
    print(f'Remaining products in store: {Product.query.filter_by(is_active=True).count()}')