from flask import Blueprint, render_template, abort, request

from app.models import Product, Category

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    featured_products = (
        Product.query.filter_by(is_active=True)
        .order_by(Product.created_at.desc())
        .limit(8)
        .all()
    )
    categories = Category.query.all()
    return render_template('index.html', products=featured_products, categories=categories)


@main_bp.route('/products')
def product_list():
    category_slug = request.args.get('category')

    query = Product.query.filter_by(is_active=True)

    if category_slug:
        category = Category.query.filter_by(slug=category_slug).first_or_404()
        query = query.filter_by(category_id=category.id)

    products = query.order_by(Product.created_at.desc()).all()
    categories = Category.query.all()

    return render_template(
        'product_list.html',
        products=products,
        categories=categories,
        active_category=category_slug,
    )


@main_bp.route('/products/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    if not product.is_active:
        abort(404)

    related_products = (
        Product.query.filter_by(category_id=product.category_id, is_active=True)
        .filter(Product.id != product.id)
        .limit(4)
        .all()
    )

    return render_template('product_detail.html', product=product, related_products=related_products)