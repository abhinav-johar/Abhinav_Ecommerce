import os
from flask import Flask, render_template 
 

from app.config import Config
from app.extensions import db, migrate, login_manager, bcrypt, csrf


def create_app():
    # templates/ lives at the project root (one level above app/),
    # not inside app/, per the project's file structure.
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    template_dir = os.path.join(base_dir, 'templates')

    app = Flask(__name__, template_folder=template_dir)
    app.config.from_object(Config)

    # ------------------------------------------------------
    # Initialize extensions
    # ------------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # ------------------------------------------------------
    # Make sure upload folders exist
    # ------------------------------------------------------
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['BANNER_FOLDER'], exist_ok=True)

    # ------------------------------------------------------
    # Import models AFTER db.init_app so tables register
    # (also required for flask-migrate to detect them)
    # ------------------------------------------------------
    from app import models  # noqa: F401

    # ------------------------------------------------------
    # Register blueprints
    # ------------------------------------------------------
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.cart import cart_bp
    from app.routes.checkout import checkout_bp
    from app.routes.orders import orders_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(cart_bp, url_prefix='/cart')
    app.register_blueprint(checkout_bp, url_prefix='/checkout')
    app.register_blueprint(orders_bp, url_prefix='/orders')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # ------------------------------------------------------
    # Error handlers
    # ------------------------------------------------------
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # ------------------------------------------------------
    # Context processor: makes category + sample-product data
    # available on every page, for the navbar mega menu
    # ------------------------------------------------------
    @app.context_processor
    def inject_nav_categories():
        from app.models import Category, Product

        categories = Category.query.all()
        nav_data = []
        for cat in categories:
            sample_products = (
                Product.query.filter_by(category_id=cat.id, is_active=True)
                .order_by(Product.created_at.desc())
                .limit(3)
                .all()
            )
            nav_data.append({'category': cat, 'products': sample_products})

        return dict(nav_categories=nav_data)

    return app