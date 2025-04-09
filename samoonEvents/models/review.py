"""Review model module.

This module defines the Review model for managing vendor reviews in the application.
It handles review data and relationships between vendors and users who create reviews.

Classes:
    Review: SQLAlchemy model for vendor reviews
"""
from ..extensions import db
from datetime import datetime


class Review(db.Model):
    """Review model class.

    Represents a review given by a user for a vendor with rating and comments.

    Attributes:
        review_id (int): Primary key
        rating (int): Numerical rating given by user
        comment (str): Optional text review
        created_at (date): Date review was created
        vendor_id (int): Foreign key to Vendor table
        user_id (int): Foreign key to User table

    Relationships:
        vendor: The vendor being reviewed
        user: The user who created the review
    """
    __tablename__ = 'Reviews'

    review_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    vendor_id = db.Column(db.Integer, db.ForeignKey('Vendor.vendor_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False)

    vendor = db.relationship('Vendor', back_populates='reviews')
    user = db.relationship('User', back_populates='reviews')

    def serialize(self):
        """Convert review instance to dictionary format.

        Returns:
            dict: Review data in serialized format
        """
        return {
            'review_id': self.review_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'vendor_id': self.vendor_id,
            'user_id': self.user_id,
        }
