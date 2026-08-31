from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
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


def is_ajax_request():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def serialize_cart(cart):
    """Build a JSON-friendly snapshot of the cart, used by the drawer."""
    items = CartItem.query.filter_by(cart_id=cart.id).all()
    subtotal = sum(item.price_at_time * item.quantity for item in items)
    count = sum(item.quantity for item in items)

    items_data = []
    for item in items:
        items_data.append({
            'id': item.id,
            'product_name': item.product.name,
            'product_image': url_for('static', filename='images/' + item.product.image_url) if item.product.image_url else None,
            'color': item.variant.color if item.variant else None,
            'size': item.variant.size if item.variant else None,
            'quantity': item.quantity,
            'price': item.price_at_time,
            'line_total': item.price_at_time * item.quantity,
        })

    return {
        'items': items_data,
        'subtotal': subtotal,
        'count': count,
        'checkout_url': url_for('checkout.checkout'),
    }


@cart_bp.route('/data', methods=['GET'])
def cart_data():
    """JSON snapshot of the current cart, used to populate the drawer."""
    user = get_current_user()
    cart = get_or_create_cart(user)
    return jsonify(serialize_cart(cart))


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
            if is_ajax_request():
                return jsonify(success=False, message='Something went wrong. Please try again.'), 400
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
            if is_ajax_request():
                return jsonify(success=False, message=f'Only {available_stock} left in stock.'), 400
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

        if is_ajax_request():
            cart_snapshot = serialize_cart(cart)
            cart_snapshot['success'] = True
            cart_snapshot['message'] = f'{product.name} added to your bag.'
            return jsonify(cart_snapshot)

        flash(f'{product.name} added to cart.', 'success')
        return redirect(url_for('cart.view_cart'))

    # GET request -> show full cart page (fallback for no-JS / direct visits)
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
    subtotal = sum(item.price_at_time * item.quantity for item in cart_items)

    return render_template('cart.html', cart_items=cart_items, subtotal=subtotal)


@cart_bp.route('/update/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    quantity = request.form.get('quantity', type=int)

    if quantity and quantity > 0:
        # Stock check
        available = item.variant.stock_quantity if item.variant else item.product.stock_quantity
        if quantity > available:
            if is_ajax_request():
                return jsonify(success=False, message=f'Only {available} left in stock.'), 400
            flash(f'Only {available} left in stock.', 'error')
            return redirect(url_for('cart.view_cart'))

        item.quantity = quantity
        db.session.commit()

        if is_ajax_request():
            cart_snapshot = serialize_cart(item.cart)
            cart_snapshot['success'] = True
            return jsonify(cart_snapshot)

        flash('Cart updated.', 'success')
    else:
        if is_ajax_request():
            return jsonify(success=False, message='Invalid quantity.'), 400
        flash('Invalid quantity.', 'error')

    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/remove/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    cart = item.cart
    db.session.delete(item)
    db.session.commit()

    if is_ajax_request():
        cart_snapshot = serialize_cart(cart)
        cart_snapshot['success'] = True
        return jsonify(cart_snapshot)

    flash('Item removed from cart.', 'success')
    return redirect(url_for('cart.view_cart'))