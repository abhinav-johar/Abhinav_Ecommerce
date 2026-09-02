from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Product, Category, Order, OrderItem, User, ProductImage
from app.utils import save_uploaded_image

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash('You do not have permission to access the admin panel.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


# ==========================================================
# DASHBOARD
# ==========================================================
@admin_bp.route('/')
@admin_required
def dashboard():
    stats = {
        'total_products': Product.query.count(),
        'active_products': Product.query.filter_by(is_active=True).count(),
        'low_stock_products': Product.query.filter(Product.stock_quantity <= 10, Product.is_active == True).count(),
        'total_orders': Order.query.count(),
        'pending_orders': Order.query.filter_by(status='pending').count(),
        'total_revenue': db.session.query(db.func.coalesce(db.func.sum(Order.total_amount), 0)).scalar(),
        'total_customers': User.query.filter_by(is_admin=False).count(),
    }
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders)


# ==========================================================
# PRODUCTS
# ==========================================================
@admin_bp.route('/products')
@admin_required
def manage_products():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/manage_product.html', products=products)


@admin_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    categories = Category.query.all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        fabric_care = request.form.get('fabric_care', '').strip() or None
        technical_specification = request.form.get('technical_specification', '').strip() or None
        warranty_info = request.form.get('warranty_info', '').strip() or None
        shipping_returns = request.form.get('shipping_returns', '').strip() or None
        price = request.form.get('price', type=float)
        discount_price = request.form.get('discount_price', type=float) or None
        stock_quantity = request.form.get('stock_quantity', type=int, default=0)
        category_id = request.form.get('category_id', type=int)
        is_active = request.form.get('is_active') == 'on'

        if not name or price is None or not category_id:
            flash('Name, price, and category are required.', 'error')
            return render_template('admin/add_product.html', categories=categories, form_data=request.form)

        image_file = request.files.get('image')
        image_url = save_uploaded_image(
            image_file,
            current_app.config['UPLOAD_FOLDER'],
            current_app.config['ALLOWED_EXTENSIONS'],
        )

        product = Product(
            name=name,
            description=description,
            fabric_care=fabric_care,
            technical_specification=technical_specification,
            warranty_info=warranty_info,
            shipping_returns=shipping_returns,
            price=price,
            discount_price=discount_price,
            stock_quantity=stock_quantity or 0,
            image_url=image_url,
            category_id=category_id,
            is_active=is_active,
        )
        db.session.add(product)
        db.session.commit()

        # Multiple gallery images (extra photos beyond the main image above)
        gallery_files = request.files.getlist('gallery_images')
        for i, gfile in enumerate(gallery_files):
            gallery_url = save_uploaded_image(
                gfile,
                current_app.config['UPLOAD_FOLDER'],
                current_app.config['ALLOWED_EXTENSIONS'],
            )
            if gallery_url:
                db.session.add(ProductImage(product_id=product.id, image_url=gallery_url, sort_order=i))
        db.session.commit()

        flash(f'"{product.name}" was added successfully.', 'success')
        return redirect(url_for('admin.manage_products'))

    return render_template('admin/add_product.html', categories=categories, form_data={})


@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.all()

    if request.method == 'POST':
        product.name = request.form.get('name', '').strip()
        product.description = request.form.get('description', '').strip()
        product.fabric_care = request.form.get('fabric_care', '').strip() or None
        product.technical_specification = request.form.get('technical_specification', '').strip() or None
        product.warranty_info = request.form.get('warranty_info', '').strip() or None
        product.shipping_returns = request.form.get('shipping_returns', '').strip() or None
        product.price = request.form.get('price', type=float)
        product.discount_price = request.form.get('discount_price', type=float) or None
        product.stock_quantity = request.form.get('stock_quantity', type=int, default=0)
        product.category_id = request.form.get('category_id', type=int)
        product.is_active = request.form.get('is_active') == 'on'

        image_file = request.files.get('image')
        new_image_url = save_uploaded_image(
            image_file,
            current_app.config['UPLOAD_FOLDER'],
            current_app.config['ALLOWED_EXTENSIONS'],
        )
        if new_image_url:
            product.image_url = new_image_url

        db.session.commit()

        # Multiple new gallery images -> append after existing ones
        gallery_files = request.files.getlist('gallery_images')
        existing_max_order = max([img.sort_order for img in product.images], default=-1)
        for i, gfile in enumerate(gallery_files):
            gallery_url = save_uploaded_image(
                gfile,
                current_app.config['UPLOAD_FOLDER'],
                current_app.config['ALLOWED_EXTENSIONS'],
            )
            if gallery_url:
                db.session.add(ProductImage(
                    product_id=product.id,
                    image_url=gallery_url,
                    sort_order=existing_max_order + 1 + i,
                ))
        db.session.commit()

        flash(f'"{product.name}" was updated.', 'success')
        return redirect(url_for('admin.manage_products'))

    return render_template('admin/add_product.html', categories=categories, product=product, form_data={})


@admin_bp.route('/products/<int:product_id>/images/<int:image_id>/delete', methods=['POST'])
@admin_required
def delete_product_image(product_id, image_id):
    image = ProductImage.query.filter_by(id=image_id, product_id=product_id).first_or_404()
    db.session.delete(image)
    db.session.commit()
    flash('Gallery image removed.', 'success')
    return redirect(url_for('admin.edit_product', product_id=product_id))


@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    try:
        db.session.delete(product)
        db.session.commit()
        flash(f'"{product.name}" was deleted.', 'success')
    except IntegrityError:
        db.session.rollback()
        # Product is referenced by past orders (OrderItem has no cascade-delete,
        # intentionally, so order history never silently loses line items).
        # Deactivating is the safe alternative to a hard delete here.
        product.is_active = False
        db.session.commit()
        flash(f'"{product.name}" is part of past orders and can\'t be deleted, so it was deactivated instead.', 'info')

    return redirect(url_for('admin.manage_products'))


@admin_bp.route('/products/<int:product_id>/toggle-active', methods=['POST'])
@admin_required
def toggle_product_active(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_active = not product.is_active
    db.session.commit()
    flash(f'"{product.name}" is now {"active" if product.is_active else "inactive"}.', 'success')
    return redirect(url_for('admin.manage_products'))


# ==========================================================
# ORDERS
# ==========================================================
@admin_bp.route('/orders')
@admin_required
def manage_orders():
    status_filter = request.args.get('status')
    query = Order.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    orders = query.order_by(Order.created_at.desc()).all()
    return render_template('admin/manage_order.html', orders=orders, status_filter=status_filter)


@admin_bp.route('/orders/<int:order_id>/update-status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    new_payment_status = request.form.get('payment_status')

    valid_statuses = {'pending', 'shipped', 'delivered', 'cancelled'}
    valid_payment_statuses = {'paid', 'unpaid', 'refunded'}

    if new_status in valid_statuses:
        order.status = new_status
    if new_payment_status in valid_payment_statuses:
        order.payment_status = new_payment_status

    db.session.commit()
    flash(f'Order #{order.id} updated.', 'success')
    return redirect(url_for('admin.manage_orders'))