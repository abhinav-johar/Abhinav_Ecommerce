from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user

from app.extensions import db
from app.models import Cart, CartItem, Order, OrderItem, Payment, Address

checkout_bp = Blueprint('checkout', __name__)


def is_ajax_request():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def get_checkout_context():
    """Returns (cart_items, subtotal, address, error_message)."""
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all() if cart else []

    if not cart_items:
        return None, None, None, 'Your cart is empty.'

    address = Address.query.filter_by(user_id=current_user.id, is_default=True).first()
    if not address:
        address = Address.query.filter_by(user_id=current_user.id).first()
    if not address:
        return None, None, None, 'Please add a delivery address before checking out.'

    subtotal = sum(item.price_at_time * item.quantity for item in cart_items)
    return cart_items, subtotal, address, None


@checkout_bp.route('/', methods=['GET'])
def checkout():
    if not current_user.is_authenticated:
        login_url = url_for('auth.login', next=url_for('checkout.checkout'))
        if is_ajax_request():
            return jsonify(success=False, needs_login=True, login_url=login_url)
        return redirect(login_url)

    cart_items, subtotal, address, error = get_checkout_context()

    if error:
        if is_ajax_request():
            return jsonify(success=False, message=error, redirect=url_for('cart.view_cart'))
        flash(error, 'error')
        return redirect(url_for('cart.view_cart'))

    if is_ajax_request():
        html = render_template(
            'fragments/checkout_content.html',
            cart_items=cart_items, subtotal=subtotal, address=address,
        )
        return jsonify(success=True, html=html)

    return render_template('checkout.html', cart_items=cart_items, subtotal=subtotal, address=address)


@checkout_bp.route('/place-order', methods=['POST'])
def place_order():
    if not current_user.is_authenticated:
        login_url = url_for('auth.login', next=url_for('checkout.checkout'))
        if is_ajax_request():
            return jsonify(success=False, needs_login=True, login_url=login_url), 401
        return redirect(login_url)

    cart_items, subtotal, address, error = get_checkout_context()

    if error:
        if is_ajax_request():
            return jsonify(success=False, message=error), 400
        flash(error, 'error')
        return redirect(url_for('cart.view_cart'))

    # Re-validate stock right before placing the order
    for item in cart_items:
        available = item.variant.stock_quantity if item.variant else item.product.stock_quantity
        if available < item.quantity:
            msg = f'{item.product.name} no longer has enough stock. Please update your cart.'
            if is_ajax_request():
                return jsonify(success=False, message=msg), 400
            flash(msg, 'error')
            return redirect(url_for('cart.view_cart'))

    total_amount = subtotal

    order = Order(
        user_id=current_user.id,
        address_id=address.id,
        total_amount=total_amount,
        status='pending',
        payment_status='unpaid',
    )
    db.session.add(order)
    db.session.flush()

    for item in cart_items:
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            variant_id=item.variant_id,
            quantity=item.quantity,
            price_at_purchase=item.price_at_time,
        ))
        if item.variant:
            item.variant.stock_quantity -= item.quantity
        else:
            item.product.stock_quantity -= item.quantity

    db.session.add(Payment(
        order_id=order.id,
        payment_method='COD',
        transaction_id=None,
        amount=total_amount,
        status='pending',
        paid_at=None,
    ))

    for item in cart_items:
        db.session.delete(item)

    db.session.commit()

    success_url = url_for('checkout.order_success', order_id=order.id)

    if is_ajax_request():
        return jsonify(success=True, redirect=success_url)

    flash('Order placed successfully!', 'success')
    return redirect(success_url)


@checkout_bp.route('/success/<int:order_id>')
def order_success(order_id):
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('You do not have access to this order.', 'error')
        return redirect(url_for('main.index'))

    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    return render_template('order_success.html', order=order, order_items=order_items)