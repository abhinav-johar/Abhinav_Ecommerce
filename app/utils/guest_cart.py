import hashlib
import secrets

from flask import current_app, request, g
from flask_login import current_user

from app.extensions import db
from app.models import Cart, CartItem, Product, ProductVariant


GUEST_CART_COOKIE = "one8_guest_cart"


def merge_guest_cart_into_user(user, raw_token):
    """
    Merge the current guest's cart into the authenticated user's cart.

    Returns:
        (merged_count, skipped_count)
    """
    if not raw_token or len(raw_token) > 128:
        return 0, 0

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    guest_cart = Cart.query.filter_by(
        guest_token_hash=token_hash,
        user_id=None
    ).first()

    if guest_cart is None:
        return 0, 0

    user_cart = Cart.query.filter_by(
        user_id=user.id
    ).first()

    if user_cart is None:
        user_cart = Cart(user_id=user.id)
        db.session.add(user_cart)
        db.session.flush()

    merged_count = 0
    skipped_count = 0

    try:
        for guest_item in list(guest_cart.items):
            product = db.session.get(
                Product, guest_item.product_id
            )

            if not product or not product.is_active:
                skipped_count += 1
                continue

            variant = None

            if guest_item.variant_id is not None:
                variant = db.session.get(
                    ProductVariant,
                    guest_item.variant_id
                )

                if (
                    variant is None
                    or variant.product_id != product.id
                ):
                    skipped_count += 1
                    continue

            available_stock = (
                variant.stock_quantity
                if variant is not None
                else product.stock_quantity
            )

            existing_item = CartItem.query.filter_by(
                cart_id=user_cart.id,
                product_id=product.id,
                variant_id=guest_item.variant_id
            ).first()

            existing_quantity = (
                existing_item.quantity
                if existing_item
                else 0
            )

            if available_stock <= existing_quantity:
                skipped_count += 1
                continue

            requested_quantity = (
                existing_quantity + guest_item.quantity
            )

            final_quantity = min(
                requested_quantity,
                available_stock
            )

            if existing_item:
                existing_item.quantity = final_quantity
            else:
                current_price = (
                    product.discount_price
                    if product.discount_price is not None
                    and product.discount_price > 0
                    else product.price
                )

                db.session.add(
                    CartItem(
                        cart_id=user_cart.id,
                        product_id=product.id,
                        variant_id=guest_item.variant_id,
                        quantity=final_quantity,
                        price_at_time=current_price
                    )
                )

            merged_count += final_quantity - existing_quantity

            if final_quantity < requested_quantity:
                skipped_count += 1

        # Remove the old guest cart after processing its items.
        db.session.delete(guest_cart)
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return merged_count, skipped_count




def clear_guest_cart_cookie(response):
    response.delete_cookie(
        GUEST_CART_COOKIE,
        path="/",
        secure=current_app.config.get(
            "SESSION_COOKIE_SECURE", False
        ),
        httponly=True,
        samesite="Lax"
    )

    return response


def get_or_create_cart():
    """
    Return the logged-in user's cart or the current guest's cart.

    Guest cookies contain a random token.
    The database stores only its SHA-256 hash.
    """

    # Authenticated users use their account-associated cart.
    if current_user.is_authenticated:
        cart = Cart.query.filter_by(user_id=current_user.id).first()

        if cart is None:
            cart = Cart(user_id=current_user.id)
            db.session.add(cart)
            db.session.commit()

        return cart

    # Reuse the cart already resolved during this request.
    if hasattr(g, "one8_guest_cart"):
        return g.one8_guest_cart

    raw_token = request.cookies.get(GUEST_CART_COOKIE)
    token_hash = None

    if raw_token and len(raw_token) <= 128:
        token_hash = hashlib.sha256(
            raw_token.encode("utf-8")
        ).hexdigest()

    cart = None

    if token_hash:
        cart = Cart.query.filter_by(
            guest_token_hash=token_hash,
            user_id=None,
        ).first()

    # Create a separate cart for a new guest.
    if cart is None:
        raw_token = secrets.token_urlsafe(32)

        token_hash = hashlib.sha256(
            raw_token.encode("utf-8")
        ).hexdigest()

        cart = Cart(guest_token_hash=token_hash)
        db.session.add(cart)
        db.session.commit()

        g.one8_guest_cart_cookie = raw_token

    g.one8_guest_cart = cart

    return cart


def set_guest_cart_cookie(response):
    """Attach the guest-cart cookie when a new token was generated."""

    raw_token = getattr(g, "one8_guest_cart_cookie", None)

    if raw_token:
        response.set_cookie(
            GUEST_CART_COOKIE,
            raw_token,
            max_age=60 * 60 * 24 * 30,
            httponly=True,
            secure=current_app.config.get("SESSION_COOKIE_SECURE", False),
            samesite="Lax",
            path="/",
        )

    return response