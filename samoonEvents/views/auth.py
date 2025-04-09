"""Authentication views for handling user login, signup, and logout."""
from flask import render_template, redirect, url_for, flash, request, current_app, session
from ..models.user import User, check_password_hash, generate_password_hash
from flask_login import login_user, logout_user, login_required
from ..extensions import db
from ..views import app_views


@app_views.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login.

    GET: Display login form
    POST: Authenticate user credentials and log them in

    Returns:
        On GET: Rendered login template
        On POST success: Redirect to dashboard
        On POST failure: Redirect to login with error message
    """
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Email and password are required', 'error')
            return redirect(url_for('app_views.login'))

        user = User.query.filter_by(email=email).first()

        if user and user.password_hash and check_password_hash(user.password_hash, password):
            login_user(user)
            # Redirect to the next page if specified, otherwise dashboard
            next_page = request.args.get('next')
            return redirect(next_page or url_for('app_views.dashboard'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('app_views.login'))

    return render_template('login.html')

@app_views.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle new user registration.

    GET: Display signup form
    POST: Create new user account

    Returns:
        On GET: Rendered signup template
        On POST success: Redirect to dashboard
        On POST failure: Redirect to signup with error message
    """
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if all required fields are provided
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return redirect(url_for('app_views.signup'))

        # Check if the user already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            if existing_user.username == username:
                flash('Username already exists', 'error')
            else:
                flash('Email address already exists', 'error')
            return redirect(url_for('app_views.signup'))

        try:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash('Account created successfully!', 'success')
            return redirect(url_for('app_views.dashboard'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Signup error: {str(e)}")
            flash('An error occurred while creating your account. Please try again.', 'error')
            return redirect(url_for('app_views.signup'))

    return render_template('signup.html')

@app_views.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    try:
        # Clear all flash messages before logging out
        session.pop('_flashes', None)

        logout_user()
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        flash('An error occurred during logout.', 'error')

    return redirect(url_for('app_views.landingpage'))
