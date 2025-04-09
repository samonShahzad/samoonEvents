"""Vendor model module.

This module defines the Vendor model for managing service providers in the application.
It handles vendor data, relationships with events and reviews, and provides methods
for serialization and rating calculations.

Classes:
    Vendor: SQLAlchemy model for vendors
"""
from ..extensions import db

"""Association table module for event-vendor relationships.

This module defines the many-to-many relationship table between events and vendors.
The table allows events to have multiple vendors and vendors to be associated with
multiple events.

Table Columns:
    event_id (int): Foreign key to Event table, part of composite primary key
    vendor_id (int): Foreign key to Vendor table, part of composite primary key
"""
event_vendors = db.Table('event_vendors',
    db.Column('event_id', db.Integer, db.ForeignKey('Event.event_id'), primary_key=True),
    db.Column('vendor_id', db.Integer, db.ForeignKey('Vendor.vendor_id'), primary_key=True),
)

class Vendor(db.Model):
    """Vendor model class.

    Represents a service provider that can be booked for events.

    Attributes:
        vendor_id (int): Primary key
        name (str): Vendor business name
        category (str): Type of service provided
        description (str): Detailed description of services
        image_path (str): Path to vendor profile image
        phone_number (str): Contact phone number
        email (str): Contact email address
        service_fee (int): Base fee for services
        rating (int): Average numerical rating
        status (str): Account status, defaults to 'pending'

    Relationships:
        reviews: Reviews received by this vendor (Review)
        events: Events this vendor is booked for (Event)
    """
    __tablename__ = 'Vendor'

    vendor_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(45), nullable=True)
    description = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(512), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    service_fee = db.Column(db.Integer, nullable=True)
    rating = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(10), default='pending')

    reviews = db.relationship('Review', back_populates='vendor')
    events = db.relationship('Event', secondary=event_vendors, back_populates='vendors')

    def serialize(self):
        """Convert vendor instance to dictionary format.

        Returns:
            dict: Vendor data in serialized format
        """
        return {
            'vendor_id': self.vendor_id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'image_path': self.image_path,
            'phone_number': self.phone_number,
            'email': self.email,
            'service_fee': self.service_fee,
            'rating': self.rating,
            'status': self.status,
            'events': [{'event_id': event.event_id,
                       'name': event.name,
                       'date': event.date} for event in self.events]
        }

    def __repr__(self):
        """String representation of Vendor instance.

        Returns:
            str: Vendor name
        """
        return f'<Vendor {self.name}>'

    @property
    def star_rating(self):
        """Get vendor's rating or 0 if not rated.

        Returns:
            int: Numerical rating value or 0
        """
        return self.rating if self.rating is not None else 0

    @property
    def average_rating(self):
        if not self.reviews:
            return None
        return sum(review.rating for review in self.reviews) / len(self.reviews)
