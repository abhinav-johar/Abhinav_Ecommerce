import hashlib
import secrets

from flask import current_app, request, g
from flask_login import current_user

from app.extensions import db
from app.models import Cart


GUEST_CART_COOKIE = "one8_guest_cart"


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