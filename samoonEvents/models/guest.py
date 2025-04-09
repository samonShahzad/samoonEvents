"""Guest model module.

This module defines the Guest model for managing event attendees in the application.
It handles guest data and relationships with events and invitations.

Classes:
    Guest: SQLAlchemy model for event guests
"""
from ..extensions import db

class Guest(db.Model):
    """Guest model class.

    Represents a guest invited to an event with properties for tracking contact
    details and attendance status.

    Attributes:
        guest_id (int): Primary key
        name (str): Guest's full name
        email (str): Guest's email address
        phone (str): Guest's phone number
        status (str): Guest's attendance status
        event_id (int): Foreign key to Event table

    Relationships:
        event: Associated event (Event)
        invitations: Guest's invitations (Invitation)
    """
    __tablename__ = 'Guest'

    guest_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(45), nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey('Event.event_id'), nullable=False)

    event = db.relationship('Event', back_populates='guests')
    invitations = db.relationship('Invitation', back_populates='guest')

    def serialize(self):
        """Convert guest instance to dictionary.

        Returns:
            dict: Guest data in serializable format
        """
        return {
            'guest_id': self.guest_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'status': self.status,
            'event_id': self.event_id,
        }

    def __repr__(self):
        """String representation of Guest instance.

        Returns:
            str: Guest name and status
        """
        return f'<Guest {self.name} (Status: {self.status})>'
