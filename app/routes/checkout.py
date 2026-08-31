from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Cart, CartItem, Order, OrderItem, Payment, Address, Product, ProductVariant

checkout_bp = Blueprint('checkout', __name__)


@checkout_bp.route('/', methods=['GET'])
@login_required
def checkout():
    user = current_user
    cart = Cart.query.filter_by(user_id=user.id).first()
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all() if cart else []

    if not cart_items:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('cart.view_cart'))

    address = Address.query.filter_by(user_id=user.id, is_default=True).first()
    if not address:
        address = Address.query.filter_by(user_id=user.id).first()

    if not address:
        flash('Please add a delivery address before checking out.', 'error')
        return redirect(url_for('cart.view_cart'))

    subtotal = sum(item.price_at_time * item.quantity for item in cart_items)

    return render_template(
        'checkout.html',
        cart_items=cart_items,
        subtotal=subtotal,
        address=address,
    )


@checkout_bp.route('/place-order', methods=['POST'])
@login_required
def place_order():
    user = current_user
    cart = Cart.query.filter_by(user_id=user.id).first()
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all() if cart else []

    if not cart_items:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('cart.view_cart'))

    address = Address.query.filter_by(user_id=user.id, is_default=True).first()
    if not address:
        address = Address.query.filter_by(user_id=user.id).first()

    if not address:
        flash('Please add a delivery address before checking out.', 'error')
        return redirect(url_for('cart.view_cart'))

    # Re-validate stock right before placing the order (in case it changed since add-to-cart)
    for item in cart_items:
        available = item.variant.stock_quantity if item.variant else item.product.stock_quantity
        if available < item.quantity:
            flash(f'{item.product.name} no longer has enough stock. Please update your cart.', 'error')
            return redirect(url_for('cart.view_cart'))

    total_amount = sum(item.price_at_time * item.quantity for item in cart_items)

    # 1. Create the Order (snapshot from cart)
    order = Order(
        user_id=user.id,
        address_id=address.id,
        total_amount=total_amount,
        status='pending',
        payment_status='unpaid',  # COD stays unpaid until delivery
    )
    db.session.add(order)
    db.session.flush()  # gets order.id without a full commit yet

    # 2. Create OrderItems from CartItems, and deduct stock
    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            variant_id=item.variant_id,
            quantity=item.quantity,
            price_at_purchase=item.price_at_time,
        )
        db.session.add(order_item)

        # Deduct stock
        if item.variant:
            item.variant.stock_quantity -= item.quantity
        else:
            item.product.stock_quantity -= item.quantity

    # 3. Create Payment record for COD
    payment = Payment(
        order_id=order.id,
        payment_method='COD',
        transaction_id=None,
        amount=total_amount,
        status='pending',
        paid_at=None,
    )
    db.session.add(payment)

    # 4. Clear the cart
    for item in cart_items:
        db.session.delete(item)

    db.session.commit()

    flash('Order placed successfully!', 'success')
    return redirect(url_for('checkout.order_success', order_id=order.id))


@checkout_bp.route('/success/<int:order_id>')
@login_required
def order_success(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('You do not have access to this order.', 'error')
        return redirect(url_for('main.index'))
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    return render_template('order_success.html', order=order, order_items=order_items)