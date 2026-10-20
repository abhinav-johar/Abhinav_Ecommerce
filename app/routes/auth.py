from flask import Blueprint, render_template, redirect, url_for, flash, request , current_app
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db, bcrypt
from app.forms import RegisterForm, LoginForm
from app.models import User, Cart, Address
from urllib.parse import urlsplit

from sqlalchemy.exc import SQLAlchemyError
from app.utils.guest_cart import (
    GUEST_CART_COOKIE,
    merge_guest_cart_into_user,
    clear_guest_cart_cookie
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegisterForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data.lower()).first()
        if existing_user:
            flash('An account with this email already exists. Please log in.', 'error')
            return redirect(url_for('auth.login'))

        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        new_user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            password_hash=hashed_pw,
            phone=form.phone.data.strip(),
            is_admin=False,
        )
        db.session.add(new_user)
        db.session.commit()

        # Every user gets exactly one cart, per your schema
        new_cart = Cart(user_id=new_user.id)
        db.session.add(new_cart)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.lower().strip()

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(
            user.password_hash,
            form.password.data
        ):
            # Step 1: Merge the guest cart BEFORE login_user().
            # At this point, current_user is still anonymous.
            guest_token = request.cookies.get(GUEST_CART_COOKIE)

            try:
                merged_count, skipped_count = merge_guest_cart_into_user(
                    user,
                    guest_token
                )

            except SQLAlchemyError:
                db.session.rollback()

                current_app.logger.exception(
                    "Database error while merging guest cart during login"
                )

                flash(
                    "We couldn't restore your cart right now. "
                    "Please try logging in again.",
                    "error"
                )

                return render_template('login.html', form=form), 500

            # Step 2: Log the user in after the cart merge succeeds.
            login_user(user, remember=form.remember.data)

            # Step 3: Notify the user about the merge, if applicable.
            if merged_count > 0:
                flash(
                    f'{merged_count} cart unit(s) restored to your account.',
                    'success'
                )

            if skipped_count > 0:
                flash(
                    f'{skipped_count} cart item(s) could not be fully '
                    'restored because of product availability or stock.',
                    'warning'
                )

            flash(f'Welcome back, {user.name}!', 'success')

            # Step 4: Only allow safe, local redirects.
            next_page = request.args.get('next')

            if next_page:
                parsed_url = urlsplit(next_page)

                if (
                    not parsed_url.scheme
                    and not parsed_url.netloc
                    and next_page.startswith('/')
                    and not next_page.startswith('//')
                    and '\\' not in next_page
                ):
                    destination = next_page
                else:
                    destination = url_for('main.index')
            else:
                destination = url_for('main.index')

            response = redirect(destination)

            # Step 5: Remove the guest-cart cookie after successful login.
            response = clear_guest_cart_cookie(response)

            return response

        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


@auth_bp.route('/addresses', methods=['GET', 'POST'])
@login_required
def addresses():
    edit_id = request.args.get('edit', type=int)
    editing_address = None
    if edit_id:
        editing_address = Address.query.filter_by(id=edit_id, user_id=current_user.id).first()

    if request.method == 'POST':
        address_id = request.form.get('address_id', type=int)  # present only when editing
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        address_line1 = request.form.get('address_line1', '').strip()
        address_line2 = request.form.get('address_line2', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        pincode = request.form.get('pincode', '').strip()
        is_default = request.form.get('is_default') == 'on'

        if not (full_name and phone and address_line1 and city and state and pincode):
            flash('Please fill in all required address fields.', 'error')
            return redirect(url_for('auth.addresses'))

        if is_default:
            Address.query.filter_by(user_id=current_user.id).update({'is_default': False})

        if address_id:
            addr = Address.query.filter_by(id=address_id, user_id=current_user.id).first_or_404()
            addr.full_name = full_name
            addr.phone = phone
            addr.address_line1 = address_line1
            addr.address_line2 = address_line2
            addr.city = city
            addr.state = state
            addr.pincode = pincode
            addr.is_default = is_default
            flash('Address updated.', 'success')
        else:
            # First address a user ever adds is automatically their default
            is_first_address = Address.query.filter_by(user_id=current_user.id).count() == 0
            new_addr = Address(
                user_id=current_user.id,
                full_name=full_name,
                phone=phone,
                address_line1=address_line1,
                address_line2=address_line2,
                city=city,
                state=state,
                pincode=pincode,
                is_default=is_default or is_first_address,
            )
            db.session.add(new_addr)
            flash('Address added.', 'success')

        db.session.commit()

        # If they arrived here from checkout (no address existed yet), send them back
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('auth.addresses'))

    user_addresses = Address.query.filter_by(user_id=current_user.id).order_by(Address.is_default.desc()).all()
    return render_template('addresses.html', addresses=user_addresses, editing_address=editing_address)


@auth_bp.route('/addresses/<int:address_id>/delete', methods=['POST'])
@login_required
def delete_address(address_id):
    addr = Address.query.filter_by(id=address_id, user_id=current_user.id).first_or_404()
    db.session.delete(addr)
    db.session.commit()
    flash('Address removed.', 'success')
    return redirect(url_for('auth.addresses'))


@auth_bp.route('/addresses/<int:address_id>/set-default', methods=['POST'])
@login_required
def set_default_address(address_id):
    addr = Address.query.filter_by(id=address_id, user_id=current_user.id).first_or_404()
    Address.query.filter_by(user_id=current_user.id).update({'is_default': False})
    addr.is_default = True
    db.session.commit()
    flash('Default address updated.', 'success')
    return redirect(url_for('auth.addresses'))