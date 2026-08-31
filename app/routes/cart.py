from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user

from app.extensions import db
from app.models import Cart, CartItem, Product, ProductVariant, User

cart_bp = Blueprint('cart', __name__)


def get_current_user():
    """
    Returns the real logged-in user if authenticated.
    Otherwise falls back to a shared 'guest' user, since Cart.user_id is
    non-nullable in the schema and true session-based guest carts aren't
    implemented. Login is required at checkout, so this only affects
    pre-login browsing/cart behavior.
    """
    if current_user.is_authenticated:
        return current_user
    return User.query.filter_by(email='test@one8.com').first()


def get_or_create_cart(user):
    cart = Cart.query.filter_by(user_id=user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.session.add(cart)
        db.session.commit()
    return cart


@cart_bp.route('/', methods=['GET', 'POST'])
def view_cart():
    user = get_current_user()
    cart = get_or_create_cart(user)

    # Handle "Add to Cart" POST coming from product_detail.html
    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        variant_id = request.form.get('variant_id', type=int) or None
        size = request.form.get('size')
        quantity = request.form.get('quantity', default=1, type=int)

        if not product_id:
            flash('Something went wrong. Please try again.', 'error')
            return redirect(url_for('cart.view_cart'))

        product = Product.query.get_or_404(product_id)

        # If the product has variants but the form only sent a size string,
        # look up the matching variant_id
        if size and not variant_id:
            variant = ProductVariant.query.filter_by(product_id=product.id, size=size).first()
            variant_id = variant.id if variant else None

        if quantity < 1:
            quantity = 1

        # Stock check
        available_stock = product.stock_quantity
        if variant_id:
            variant = ProductVariant.query.get(variant_id)
            if variant:
                available_stock = variant.stock_quantity

        if available_stock < quantity:
            flash(f'Only {available_stock} left in stock.', 'error')
            return redirect(url_for('main.product_detail', product_id=product.id))

        # Check if this exact product+variant is already in the cart -> increase quantity
        existing_item = CartItem.query.filter_by(
            cart_id=cart.id, product_id=product.id, variant_id=variant_id
        ).first()

        if existing_item:
            existing_item.quantity += quantity
        else:
            price_to_use = product.discount_price if product.discount_price else product.price
            new_item = CartItem(
                cart_id=cart.id,
                product_id=product.id,
                variant_id=variant_id,
                quantity=quantity,
                price_at_time=price_to_use,
            )
            db.session.add(new_item)

        db.session.commit()
        flash(f'{product.name} added to cart.', 'success')
        return redirect(url_for('cart.view_cart'))

    # GET request -> show cart contents
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
    subtotal = sum(item.price_at_time * item.quantity for item in cart_items)

    return render_template('cart.html', cart_items=cart_items, subtotal=subtotal)


@cart_bp.route('/update/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    quantity = request.form.get('quantity', type=int)

    if quantity and quantity > 0:
        item.quantity = quantity
        db.session.commit()
        flash('Cart updated.', 'success')
    else:
        flash('Invalid quantity.', 'error')

    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/remove/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item removed from cart.', 'success')
    return redirect(url_for('cart.view_cart'))