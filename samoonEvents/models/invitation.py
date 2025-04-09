"""Invitation model module.

This module defines the Invitation model for managing event invitations in the application.
It handles the relationship between guests and events, tracking invitation status and
providing serialization methods.

Classes:
    Invitation: SQLAlchemy model for invitations
"""
from ..extensions import db

class Invitation(db.Model):
    """Invitation model class.

    Represents an invitation in the system linking guests to events and tracking
    their RSVP status.

    Attributes:
        invitation_id (int): Primary key
        status (str): Current invitation status (default: 'Pending')
        guest_id (int): Foreign key to Guest table
        event_id (int): Foreign key to Event table

    Relationships:
        guest: Associated guest (Guest)
        event: Associated event (Event)
    """
    __tablename__ = 'Invitation'

    invitation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    status = db.Column(db.String(45), nullable=False, default='Pending')
    guest_id = db.Column(db.Integer, db.ForeignKey('Guest.guest_id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('Event.event_id'), nullable=False)

    guest = db.relationship('Guest', back_populates='invitations')
    event = db.relationship('Event', back_populates='invitations')

    def serialize(self):
        """Convert invitation object to dictionary.

        Returns:
            dict: Dictionary containing invitation data
        """
        return {
            'invitation_id': self.invitation_id,
            'status': self.status,
            'guest_id': self.guest_id,
            'event_id': self.event_id,
        }

    def __repr__(self):
        """String representation of Invitation object.

        Returns:
            str: Formatted string with invitation details
        """
        return f'<Invitation {self.invitation_id} (Status: {self.status})>'
