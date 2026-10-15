from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models import Order, OrderItem

orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/')
@login_required
def order_history():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders)


@orders_bp.route('/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('You do not have access to this order.', 'error')
        return redirect(url_for('orders.order_history'))

    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    return render_template('order_detail.html', order=order, order_items=order_items)