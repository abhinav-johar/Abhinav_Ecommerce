from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    jsonify,
    make_response,
)
from flask_login import current_user

from app.extensions import db
from app.models import Cart, CartItem, Product, ProductVariant
from app.utils.guest_cart import (
    get_or_create_cart,
    set_guest_cart_cookie,
)

cart_bp = Blueprint('cart', __name__)


 


 
def get_owned_cart_item_or_404(item_id):
    """Return an item only if it belongs to the current user's cart."""

    cart = get_or_create_cart()

    return CartItem.query.filter_by(
        id=item_id,
        cart_id=cart.id,
    ).first_or_404()

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

    cart = get_or_create_cart()

    response = make_response(jsonify(serialize_cart(cart)))

    return set_guest_cart_cookie(response)


@cart_bp.route('/', methods=['GET', 'POST'])
def view_cart():
    cart = get_or_create_cart()

    # Handle "Add to Cart" POST coming from product_detail.html
    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        variant_id = request.form.get('variant_id', type=int) or None
        size = request.form.get('size')
        quantity = request.form.get('quantity', default=1, type=int)

        if not product_id:
            if is_ajax_request():
                response = make_response(jsonify(
                    success=False,
                    message='Something went wrong. Please try again.'
                ), 400)
                return set_guest_cart_cookie(response)

            flash('Something went wrong. Please try again.', 'error')
            response = make_response(redirect(url_for('cart.view_cart')))
            return set_guest_cart_cookie(response)

        product = Product.query.get_or_404(product_id)

        # Find the matching variant if only the size was submitted
        # Resolve the exact selected product variant using colour and size.
        color = request.form.get('color', '').strip()

        if not variant_id and (size or color):
            variant_query = ProductVariant.query.filter_by(
                product_id=product.id,
                size=size or None,
                color=color or None
    )

            variant = variant_query.first()
            variant_id = variant.id if variant else None

# Reject a selection that does not correspond to a real variant.
        if (size or color) and not variant_id:
            response = make_response(jsonify(
                success=False,
                message='The selected colour and size combination is unavailable.'
               ), 400)
            return set_guest_cart_cookie(response)

        if quantity < 1:
            quantity = 1

        # Stock check
        available_stock = product.stock_quantity

        if variant_id:
            variant = ProductVariant.query.filter_by(
                id=variant_id,
                product_id=product.id
            ).first()

            if not variant:
                response = make_response(jsonify(
                    success=False,
                    message='Invalid product variant.'
                ), 400)
                return set_guest_cart_cookie(response)

            available_stock = variant.stock_quantity

        if available_stock < quantity:
            if is_ajax_request():
                response = make_response(jsonify(
                    success=False,
                    message=f'Only {available_stock} left in stock.'
                ), 400)
                return set_guest_cart_cookie(response)

            flash(f'Only {available_stock} left in stock.', 'error')
            response = make_response(
                redirect(url_for('main.product_detail', product_id=product.id))
            )
            return set_guest_cart_cookie(response)

        # Find an existing item with the same product and variant
        existing_item = CartItem.query.filter_by(
            cart_id=cart.id,
            product_id=product.id,
            variant_id=variant_id
        ).first()

        if existing_item:
            if existing_item.quantity + quantity > available_stock:
                if is_ajax_request():
                    response = make_response(jsonify(
                        success=False,
                        message=f'Only {available_stock} left in stock.'
                    ), 400)
                    return set_guest_cart_cookie(response)

                flash(f'Only {available_stock} left in stock.', 'error')
                response = make_response(redirect(url_for('cart.view_cart')))
                return set_guest_cart_cookie(response)

            existing_item.quantity += quantity

        else:
            price_to_use = (
                product.discount_price
                if product.discount_price
                else product.price
            )

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

            response = make_response(jsonify(cart_snapshot))
            return set_guest_cart_cookie(response)

        flash(f'{product.name} added to cart.', 'success')
        response = make_response(redirect(url_for('cart.view_cart')))
        return set_guest_cart_cookie(response)

    # GET request: display the full cart page
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
    subtotal = sum(item.price_at_time * item.quantity for item in cart_items)

    response = make_response(
        render_template(
            'cart.html',
            cart_items=cart_items,
            subtotal=subtotal,
        )
    )

    return set_guest_cart_cookie(response)


@cart_bp.route('/update/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    item = get_owned_cart_item_or_404(item_id)
    quantity = request.form.get('quantity', type=int)

    if quantity and quantity > 0:
        available = (
            item.variant.stock_quantity
            if item.variant
            else item.product.stock_quantity
        )

        if quantity > available:
            if is_ajax_request():
                response = make_response(jsonify(
                    success=False,
                    message=f'Only {available} left in stock.'
                ), 400)
                return set_guest_cart_cookie(response)

            flash(f'Only {available} left in stock.', 'error')
            response = make_response(redirect(url_for('cart.view_cart')))
            return set_guest_cart_cookie(response)

        item.quantity = quantity
        db.session.commit()

        if is_ajax_request():
            cart_snapshot = serialize_cart(item.cart)
            cart_snapshot['success'] = True

            response = make_response(jsonify(cart_snapshot))
            return set_guest_cart_cookie(response)

        flash('Cart updated.', 'success')

    else:
        if is_ajax_request():
            response = make_response(jsonify(
                success=False,
                message='Invalid quantity.'
            ), 400)
            return set_guest_cart_cookie(response)

        flash('Invalid quantity.', 'error')

    response = make_response(redirect(url_for('cart.view_cart')))
    return set_guest_cart_cookie(response)


@cart_bp.route('/remove/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    item = get_owned_cart_item_or_404(item_id)
    cart = item.cart

    db.session.delete(item)
    db.session.commit()

    if is_ajax_request():
        cart_snapshot = serialize_cart(cart)
        cart_snapshot['success'] = True

        response = make_response(jsonify(cart_snapshot))
        return set_guest_cart_cookie(response)

    flash('Item removed from cart.', 'success')

    response = make_response(redirect(url_for('cart.view_cart')))
    return set_guest_cart_cookie(response)