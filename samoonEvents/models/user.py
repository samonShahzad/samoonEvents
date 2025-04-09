"""User model module.

This module defines the User model for managing user accounts in the application.
It handles user authentication, profile data, and relationships with events and reviews.

Classes:
    User: SQLAlchemy model for users with authentication capabilities
"""
from ..extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    """User model class.

    Represents a user account with authentication and profile capabilities.
    Inherits from UserMixin to provide Flask-Login functionality.

    Attributes:
        user_id (int): Primary key
        username (str): Unique username
        email (str): Unique email address
        password_hash (str): Hashed password
        profile_picture (str): Path to profile picture file

    Relationships:
        events: Events owned by this user (Event)
        reviews: Reviews written by this user (Review)
    """
    __tablename__ = 'User'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    profile_picture = db.Column(db.String(512), nullable=True, default='default_profile.jpg')

    events = db.relationship('Event', back_populates='owner', lazy='dynamic')
    reviews = db.relationship('Review', back_populates='user', lazy='dynamic')

    def get_id(self):
        """Get user ID for Flask-Login."""
        return self.user_id

    def set_password(self, password):
        """Hash and set user password.

        Args:
            password (str): Plain text password to hash and store
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify a password against the stored hash.

        Args:
            password (str): Plain text password to verify

        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)

    def serialize(self):
        """Convert user object to dictionary for API responses.

        Returns:
            dict: User data excluding sensitive fields
        """
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
        }

    def __repr__(self):
        """String representation of User object."""
        return f'<User {self.username}>'
