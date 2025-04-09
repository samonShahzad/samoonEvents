"""Profile and account management views.

This module handles user profile, settings, landing page and about page routes.
It manages authentication redirects and template rendering for these core pages.
"""
from flask import render_template, redirect, url_for, jsonify, request, current_app, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from .views import app_views
from ..models import User
from ..extensions import db
from flask_login import logout_user
from datetime import datetime
from ..config import Config


@app_views.route('/')
def landingpage():
    """Handle the main landing page route.

    If user is already authenticated, redirects to their dashboard.
    Otherwise displays the landing page.

    Returns:
        Response: Redirects to dashboard for authenticated users,
                 otherwise renders landing page template
    """
    if current_user.is_authenticated:
        return redirect(url_for('app_views.dashboard'))
    return render_template('landingpage.html')


@app_views.route('/about')
def about():
    """Handle the about page route.

    Displays general information about the application.

    Returns:
        Response: Rendered about page template
    """
    return render_template('about.html')


@app_views.route('/profile', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def profile():
    """Handle user profile operations.

    GET: Display profile page
    POST: Update profile picture
    PUT: Update profile information
    DELETE: Delete user account
    """
    if request.method == 'GET':
        return render_template('profile.html')

    elif request.method == 'POST':
        if 'profile_picture' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        # Get file from request
        file = request.files['profile_picture']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Check file size
        if request.content_length > Config.MAX_CONTENT_LENGTH:
            return jsonify({'error': f'File too large. Maximum size is {Config.MAX_CONTENT_LENGTH // (1024 * 1024)}MB'}), 413

        # Check file extension
        if file and allowed_file(file.filename):
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secure_filename(file.filename)}"
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
            file.save(file_path)

            current_user.profile_picture = filename
            db.session.commit()

            return jsonify({'message': 'Profile picture updated successfully'})

        return jsonify({'error': 'Invalid file type'}), 400

    elif request.method == 'PUT':
        data = request.get_json()

        if 'username' in data and data['username'] != current_user.username:
            if User.query.filter_by(username=data['username']).first():
                return jsonify({'error': 'Username already taken'}), 400
            current_user.username = data['username']

        if 'email' in data and data['email'] != current_user.email:
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'error': 'Email already taken'}), 400
            current_user.email = data['email']

        if 'new_password' in data and data['new_password']:
            current_user.set_password(data['new_password'])

        db.session.commit()
        return jsonify({'message': 'Profile updated successfully'})

    elif request.method == 'DELETE':
        db.session.delete(current_user)
        db.session.commit()
        logout_user()
        return jsonify({'message': 'Account deleted successfully'})


@app_views.route('/settings', methods=['GET', 'PUT'])
@login_required
def settings():
    """Handle the user settings page route.

    GET: Display settings page
    PUT: Update user settings preferences

    Returns:
        GET: Rendered settings page template
        PUT: JSON response with success/error message
    """
    if request.method == 'GET':
        # Get user settings from session or use defaults
        user_settings = session.get('user_settings', {
            'emailNotifications': False,
            'eventReminders': False,
            'defaultReminder': '30',
            'darkMode': False
        })
        return render_template('settings.html', user_settings=user_settings)

    elif request.method == 'PUT':
        try:
            data = request.get_json()

            # Store settings in user session
            session['user_settings'] = {
                'emailNotifications': data.get('emailNotifications', False),
                'eventReminders': data.get('eventReminders', False),
                'defaultReminder': data.get('defaultReminder', '30'),
                'darkMode': data.get('darkMode', False)
            }

            return jsonify({
                'message': 'Settings saved successfully',
                'darkMode': session['user_settings']['darkMode']
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 400


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
