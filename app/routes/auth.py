from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db, bcrypt
from app.forms import RegisterForm, LoginForm
from app.models import User, Cart

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
        user = User.query.filter_by(
            email=form.email.data.lower().strip()
        ).first()

        # Check if email exists
        if not user:
            flash('Email does not exist.', 'error')

        # Email exists, now check password
        elif not bcrypt.check_password_hash(
            user.password_hash,
            form.password.data
        ):
            flash('Wrong password.', 'error')

        # Email and password are correct
        else:
            login_user(user, remember=form.remember.data)
            flash(f'Welcome back, {user.name}!', 'success')

            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(
                url_for('main.index')
            )

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